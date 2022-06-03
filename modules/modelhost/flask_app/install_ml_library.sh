# Check if ML_LIBRARY is set. If not, pass.
if [ -z "${DEPLOY_ENV}" ];
then
        echo 'No Model Library specified, installing supported latest versions libraries...'
        pip install onnxruntime
        pip install tensorflow

else
        pip install $ML_LIBRARY
fi