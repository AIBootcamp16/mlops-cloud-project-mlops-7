"""S3 기반 기상 데이터 파싱 및 전처리기"""
from __future__ import annotations

import sys
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

# 프로젝트 루트 경로 세팅
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger_config import configure_logger
from src.data.kma_client import KMAApiClient
from src.utils.config import KMAApiConfig, S3Config
from src.storage.s3_client import S3StorageClient
from src.storage.s3_client import WeatherDataS3Handler
from src.features.feature_builder import create_ml_dataset

# ✅ WeatherParser → parsers 로 변경
from src.data import parsers

_logger = configure_logger(__name__)


class WeatherDataProcessor:
    """S3 기반 기상 데이터 파싱 및 전처리기"""

    def __init__(self, kma_config: KMAApiConfig = None, s3_config: S3Config = None):
        self._logger = configure_logger(self.__class__.__name__)

        if kma_config is None:
            kma_config = KMAApiConfig.from_env()
        if s3_config is None:
            s3_config = S3Config.from_env()

        # KMA API 클라이언트 초기화
        self.kma_client = KMAApiClient(kma_config)

        # S3 클라이언트 초기화
        self.s3_client = S3StorageClient(
            bucket_name=s3_config.bucket_name,
            aws_access_key_id=s3_config.aws_access_key_id,
            aws_secret_access_key=s3_config.aws_secret_access_key,
            region_name=s3_config.region_name,
            endpoint_url=s3_config.endpoint_url,  # LocalStack 사용 가능
        )
        self.weather_handler = WeatherDataS3Handler(self.s3_client)

    def process_and_store_weather_data(
        self,
        asos_raw: str = None,
        pm10_raw: str = None,
        timestamp: datetime = None,
    ) -> Dict[str, str]:
        """원시 기상 데이터를 파싱하고 S3에 저장"""

        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)

        self._logger.info("Starting weather data processing and S3 storage")

        try:
            stored_keys = {}

            # 1. 원시 데이터 S3 저장
            if asos_raw:
                stored_keys["asos_raw"] = self.weather_handler.save_raw_weather_data("asos", asos_raw, timestamp)
            if pm10_raw:
                stored_keys["pm10_raw"] = self.weather_handler.save_raw_weather_data("pm10", pm10_raw, timestamp)

            # 2. 데이터 파싱 (✅ parsers 모듈 함수 사용)
            parsed_asos = parsers.parse_asos_raw(asos_raw) if asos_raw else []
            parsed_pm10 = parsers.parse_pm10_raw(pm10_raw) if pm10_raw else []

            # 3. 파싱된 데이터 S3 저장
            if parsed_asos:
                stored_keys["asos_parsed"] = self.weather_handler.save_parsed_weather_data("asos", parsed_asos, timestamp)
            if parsed_pm10:
                stored_keys["pm10_parsed"] = self.weather_handler.save_parsed_weather_data("pm10", parsed_pm10, timestamp)

            # 4. ML용 데이터셋 생성 및 저장
            if parsed_asos or parsed_pm10:
                raw_data = {"asos": parsed_asos, "pm10": parsed_pm10}
                ml_dataset = create_ml_dataset(raw_data, include_labels=False)  # 실시간 추론용: 정답 제외

                if not ml_dataset.empty:
                    ml_key = self.weather_handler.save_ml_dataset(ml_dataset, timestamp)
                    stored_keys["ml_dataset"] = ml_key
                    self._logger.info(f"ML 데이터셋 저장 완료: {ml_dataset.shape}")
                else:
                    self._logger.warning("ML 데이터셋이 비어있습니다.")

            return stored_keys

        except Exception as e:
            self._logger.error(f"Error in weather data processing: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def load_latest_ml_dataset(self, days_back: int = 7) -> Optional[pd.DataFrame]:
        """최신 ML 데이터셋 로드"""
        return self.weather_handler.load_latest_ml_dataset(days_back=days_back)

    def get_data_inventory(self) -> Dict[str, Any]:
        """S3 데이터 인벤토리 조회"""
        return self.weather_handler.get_data_inventory()

    def update_master_training_dataset(
        self,
        new_data_df: pd.DataFrame,
        master_key: str = "weather_pm10_integrated_full.csv",
        retention_days: int = 630
    ) -> Dict[str, str]:
        """
        마스터 학습 데이터셋을 Rolling Window 방식으로 업데이트합니다.

        Args:
            new_data_df: 새로 추가할 데이터 (현재 시간의 기상 데이터)
            master_key: S3에 저장된 마스터 파일 키
            retention_days: 데이터 보존 기간 (일수, 기본 21개월/630일)

        Returns:
            업데이트된 S3 키 정보
        """
        try:
            self._logger.info("마스터 학습 데이터셋 Rolling Window 업데이트 시작")

            # 1. S3에서 기존 마스터 데이터 다운로드
            try:
                existing_df = self.weather_handler.load_csv_from_s3(master_key)
                self._logger.info(f"기존 마스터 데이터 로드: {len(existing_df)} 레코드")
            except Exception as e:
                # 마스터 파일이 없는 경우 빈 DataFrame으로 시작
                self._logger.warning(f"기존 마스터 데이터 없음, 새로 생성: {e}")
                existing_df = pd.DataFrame()

            # 2. 새 데이터와 기존 데이터 병합
            if not existing_df.empty and not new_data_df.empty:
                # datetime 컬럼이 있는지 확인 후 변환
                if 'datetime' in existing_df.columns:
                    existing_df['datetime'] = pd.to_datetime(existing_df['datetime'])
                if 'datetime' in new_data_df.columns:
                    new_data_df['datetime'] = pd.to_datetime(new_data_df['datetime'])

                # 데이터 병합
                merged_df = pd.concat([existing_df, new_data_df], ignore_index=True)
            elif not new_data_df.empty:
                merged_df = new_data_df.copy()
                if 'datetime' in merged_df.columns:
                    merged_df['datetime'] = pd.to_datetime(merged_df['datetime'])
            else:
                self._logger.warning("새 데이터가 없어 업데이트를 건너뜁니다")
                return {"status": "skipped", "reason": "no_new_data"}

            # 3. Rolling Window 적용 (21개월치 데이터만 유지)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            before_count = len(merged_df)

            if 'datetime' in merged_df.columns:
                merged_df = merged_df[merged_df['datetime'] >= cutoff_date]

            # 4. 중복 제거 (datetime + station_id 기준)
            duplicate_columns = ['datetime']
            if 'station_id' in merged_df.columns:
                duplicate_columns.append('station_id')

            merged_df = merged_df.drop_duplicates(subset=duplicate_columns, keep='last')
            merged_df = merged_df.sort_values(['datetime', 'station_id'] if 'station_id' in merged_df.columns else ['datetime'])
            merged_df = merged_df.reset_index(drop=True)

            after_count = len(merged_df)
            removed_count = before_count - after_count

            self._logger.info(f"Rolling Window 적용 완료: {before_count} → {after_count} (-{removed_count} 레코드)")

            # 5. S3에 업데이트된 마스터 데이터 업로드
            updated_key = self.weather_handler.save_csv_to_s3(merged_df, master_key)

            # 6. 업데이트된 데이터로 ML 학습용 데이터셋 생성
            ml_training_key = None
            if not merged_df.empty:
                # 기존 데이터를 feature_builder 형식으로 변환
                raw_data_for_ml = self._convert_csv_to_feature_format(merged_df)
                if raw_data_for_ml:
                    ml_dataset = create_ml_dataset(raw_data_for_ml, include_labels=True)  # 학습용: 정답 포함
                    if not ml_dataset.empty:
                        ml_training_key = self.weather_handler.save_ml_dataset(
                            ml_dataset,
                            datetime.now(),
                            key_suffix="training_master"
                        )
                        self._logger.info(f"ML 학습용 데이터셋 업데이트 완료: {ml_dataset.shape}")

            return {
                "master_dataset": updated_key,
                "ml_training_dataset": ml_training_key,
                "records_before": before_count,
                "records_after": after_count,
                "records_removed": removed_count,
                "retention_cutoff": cutoff_date.isoformat()
            }

        except Exception as e:
            self._logger.error(f"마스터 데이터셋 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}

    def _convert_csv_to_feature_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """CSV 형태의 데이터를 feature_builder가 기대하는 형식으로 변환"""
        try:
            asos_records = []
            pm10_records = []

            for _, row in df.iterrows():
                # ASOS 데이터 (온도)
                if pd.notna(row.get('temperature')) or pd.notna(row.get('TA')):
                    temp_value = row.get('temperature') or row.get('TA')
                    asos_records.append({
                        "station_id": str(row.get('STN', row.get('station_id', 'unknown'))),
                        "observed_at": row.get('datetime'),
                        "category": "asos",
                        "value": temp_value,
                        "unit": "°C"
                    })

                # PM10 데이터
                if pd.notna(row.get('pm10')) or pd.notna(row.get('PM10')):
                    pm10_value = row.get('pm10') or row.get('PM10')
                    pm10_records.append({
                        "station_id": str(row.get('STN', row.get('station_id', 'unknown'))),
                        "observed_at": row.get('datetime'),
                        "category": "pm10",
                        "value": pm10_value,
                        "unit": "μg/m³"
                    })

            return {
                "asos": asos_records,
                "pm10": pm10_records
            }

        except Exception as e:
            self._logger.error(f"데이터 형식 변환 실패: {e}")
            return {"asos": [], "pm10": []}

    def fetch_weather_data(self, data_type: str) -> str:
        """KMA API에서 특정 타입의 기상 데이터 수집"""
        target_time = datetime.now() - timedelta(hours=1)

        try:
            if data_type == 'asos':
                return self.kma_client.fetch_asos(target_time)
            elif data_type == 'pm10':
                return self.kma_client.fetch_pm10(target_time, target_time)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            self._logger.error(f"Error fetching {data_type} data: {e}")
            return ""

    def parse_weather_data(self, data_type: str, raw_data: str) -> list:
        """원시 기상 데이터 파싱"""
        try:
            if data_type == 'asos':
                return parsers.parse_asos_raw(raw_data)
            elif data_type == 'pm10':
                return parsers.parse_pm10_raw(raw_data)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            self._logger.error(f"Error parsing {data_type} data: {e}")
            return []


def main():
    print("S3 기반 기상 데이터 처리기")
    print("=" * 50)

    try:
        kma_config = KMAApiConfig.from_env()
        s3_config = S3Config.from_env()

        client = KMAApiClient(kma_config)
        target_time = datetime.now() - timedelta(hours=1)

        asos_raw = client.fetch_asos(target_time)
        pm10_raw = client.fetch_pm10(target_time, target_time)

        processor = WeatherDataProcessor(kma_config, s3_config)

        # 1. 실시간 데이터 처리 및 저장 (기존 로직)
        stored_keys = processor.process_and_store_weather_data(
            asos_raw=asos_raw, pm10_raw=pm10_raw, timestamp=target_time
        )

        # 2. 마스터 학습 데이터셋 Rolling Window 업데이트 (새 로직)
        if stored_keys:
            print(f"\n실시간 데이터 처리 완료! 저장된 객체 수: {len(stored_keys)}")
            print("마스터 학습 데이터셋 업데이트 시작...")

            # 현재 시간의 데이터를 DataFrame으로 변환
            current_data = []
            parsed_asos = parsers.parse_asos_raw(asos_raw) if asos_raw else []
            parsed_pm10 = parsers.parse_pm10_raw(pm10_raw) if pm10_raw else []

            # 통합 레코드 생성 (CSV 형식)
            for asos_record in parsed_asos:
                current_data.append({
                    'datetime': asos_record.get('observed_at'),
                    'STN': asos_record.get('station_id'),
                    'temperature': asos_record.get('value'),
                    'pm10': None
                })

            for pm10_record in parsed_pm10:
                # 같은 시간/스테이션의 기존 레코드를 찾아서 PM10 값 추가
                found = False
                for record in current_data:
                    if (record['datetime'] == pm10_record.get('observed_at') and
                        record['STN'] == pm10_record.get('station_id')):
                        record['pm10'] = pm10_record.get('value')
                        found = True
                        break

                if not found:
                    current_data.append({
                        'datetime': pm10_record.get('observed_at'),
                        'STN': pm10_record.get('station_id'),
                        'temperature': None,
                        'pm10': pm10_record.get('value')
                    })

            if current_data:
                new_data_df = pd.DataFrame(current_data)

                # 마스터 데이터셋 업데이트
                update_result = processor.update_master_training_dataset(new_data_df)

                if update_result.get("status") != "failed":
                    print(f"✅ 마스터 데이터셋 업데이트 완료:")
                    print(f"   - 업데이트 전: {update_result.get('records_before', 0):,} 레코드")
                    print(f"   - 업데이트 후: {update_result.get('records_after', 0):,} 레코드")
                    print(f"   - 제거된 레코드: {update_result.get('records_removed', 0):,} (오래된 데이터)")
                    if update_result.get('ml_training_dataset'):
                        print(f"   - ML 학습용 데이터셋도 업데이트됨")
                else:
                    print(f"❌ 마스터 데이터셋 업데이트 실패: {update_result.get('error')}")
            else:
                print("⚠️ 현재 시간 데이터가 없어 마스터 업데이트를 건너뜁니다")
        else:
            print("처리된 데이터가 없습니다.")

        return stored_keys
    except Exception as e:
        print(f"오류 발생: {e}")
        return {}


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)


__all__ = ["WeatherDataProcessor"]