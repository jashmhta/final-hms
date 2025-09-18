FROM node:22-alpine
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev
COPY index.mjs ./index.mjs
EXPOSE 9020
CMD ["npm", "start"]