FROM nginx:alpine
# Copy your code
COPY . /usr/share/nginx/html
# Copy the new config
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80