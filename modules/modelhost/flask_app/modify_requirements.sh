# Check if ML_LIBRARY is set. If not, pass.
if [${ML_LIBRARY-""} == ""]
then
        echo 'No Model Library specified, installing latest version of detected library...'
else
        pip install -y $ML_LIBRARY
fi
