# Imagen del frontend en dos etapas. Se construye con: docker compose build frontend

# Etapa 1: compila React con Node (esta etapa no queda en la imagen final).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Etapa 2: nginx sirve el resultado de la compilación (carpeta dist/).
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
