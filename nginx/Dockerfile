# nginx/Dockerfile
FROM nginx:latest

# Copiar el archivo de configuración de Nginx
# Now, nginx.conf is at ./nginx/nginx.conf relative to the root context
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

# Copia la carpeta 'static' de Flask, ahora directamente accesible desde el root context
COPY ./flask/static /app/static

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
