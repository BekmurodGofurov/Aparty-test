const http = require('http');
http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    console.log("APP_ERROR:", body);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.end('ok');
  });
}).listen(4444, () => console.log('Listening for errors on 4444...'));
