FROM node:26.5-alpine AS builder

WORKDIR /app

COPY package*.json /app/

RUN npm install;

COPY . .

RUN npm run build


FROM nginx:1.31.3-alpine
LABEL authors="irudenko"

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
