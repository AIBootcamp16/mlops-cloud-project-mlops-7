# Node.js 18 LTS 이미지 사용
FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치 (충돌 해결을 위해 npm install 사용)
RUN npm install

# 소스 코드 복사
COPY . .

# 포트 3000 노출
EXPOSE 3000

# 개발 서버 실행 (hot reload 지원)
CMD ["npm", "run", "dev"] 