FROM node:24.16-alpine AS builder

WORKDIR /app

COPY package*.json /app/

RUN npm install;

COPY . .

RUN npm run build


FROM nginx:1.30.2-alpine
LABEL authors="irudenko"

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
