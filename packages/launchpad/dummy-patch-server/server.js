const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;

const requestHandler = (request, response) => {
  console.log('Patch Server Request:', request.url);
  
  // Set CORS headers
  response.setHeader('Access-Control-Allow-Origin', '*');
  
  let filePath = path.join(__dirname, request.url === '/' ? 'manifest.json' : request.url);
  
  fs.readFile(filePath, (err, data) => {
    if (err) {
      response.writeHead(404);
      response.end(JSON.stringify(err));
      return;
    }
    
    response.writeHead(200);
    response.end(data);
  });
};

const server = http.createServer(requestHandler);

server.listen(PORT, (err) => {
  if (err) {
    return console.log('Error:', err);
  }
  console.log(`Serveur de Patch Simulatif en ligne sur http://127.0.0.1:${PORT}`);
});
