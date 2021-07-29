#!/bin/bash

echo 'Thanks for use FractalMLServer-Lite. The server will be stopped'
cd FractalMLServer-Lite/deploy
exec docker-compose down 
echo 'FractalServer-Lite stopped'
echo 'Bye...'
