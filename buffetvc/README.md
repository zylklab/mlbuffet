# BUFFETVC (BUFFET Version Control)

![](img/BUFFET-VC.png)

Buffet-VC (nombre provisional, sujeto a cambios) es una prueba de concepto de lo que sería un control de versiones de archivos, similar a DVC, pero gestionando todo el histórico de las versiones, pudiendo volver a versiones anteriores (cosa que DVC no hace por sí solo). Además, está implementado en Python, cosa que la PythonAPI de DVC tampoco hace.

> Cualquier crítica o idea es bienvenida. Lo que creáis conveniente que se deba implementar o que os parezca interesante comentadlo.
> 
> Así mismo, si veis que algo no merece la pena, que está mal implementado, o que se puede mejorar, comentadlo cuanto antes.

Ahora mismo, está en una versión pre-pre-pre-alpha. Únicamente tenemos dos métodos:

* `save_file`
* `remove_file`

## CAMBIO DE CONCEPTO

Hasta ahora, hemos estado gestionando los archivos de forma que el nombre del archivo del modelo (_p.e. iris.onnx_) al propio modelo. Ahora esto se desacopla, ya que tenemos:

* `etiqueta` Sería el nombre asociado al modelo, sin extensiones. (p.e. _iris, dog_model, etc_). Cuando se borre el modelo, se le puede añadir la versión separada con dos puntos si se quiere especificar la versión concreta (_iris:default, dogmodel:2_).
* `nombre_archivo` El nombre en sí del archivo del modelo, con extensiones. (p.e. _irisv1.onnx, dogmodel_finalversion.onnx_)

Cuando se lea los métodos, seguramente se entienda mejor.

Para hacer las pruebas, hay que estar seguros de que existe la carpeta `/archivos`. Si no, peta

### `save_file`

Para guardar un archivo (independientemente de la extensión) se utiliza el comando:

```commandline
curl -X PUT -F "path=@<nombre_archivo>" http://localhost:5000/save/<etiqueta>
```

Por ejemplo:

```commandline
curl -X PUT -F "path=@probefile.txt" http://localhost:5000/save/hello
```
> AVISO: En este caso, el método automáticamente asigna la versión, no hay que indicársela en la `etiqueta`

Si miramos los archivos, vemos que ahora tenemos:
```shell
archivos/
└── hello
    ├── 1
    │   └── probefile.txt
    ├── .history
    └── .default

```
El archivo `probefile.txt` ha sido guardado con la etiqueta asignada `hello` y como es la primera versión, en este caso está guardado en la carpeta `1`. Además, se han generado dos archivos:
* `.history` Contiene el histórico de los archivos que existen en la carpeta `hello`.
* `.default` Contiene la versión del último archivo guardado
Si lanzamos el mismo comando 3 veces más, obtenemos lo siguiente:
```shell
archivos/
└── hello
    ├── 1
    │   └── probefile.txt
    ├── 2
    │   └── probefile.txt
    ├── 3
    │   └── probefile.txt
    ├── 4
    │   └── probefile.txt
    ├── .history
    └── .default

```
Cada archivo se ha guardado dentro de la carpeta `hello` en la carpeta de su versión correspondiente.
Además, este es el contendio del archivo `.history`:
```json
{
  "1": {
    "file": "probefile.txt",
    "folder": "archivos/hello/1",
    "time": "09:08:02 11/03/2022",
    "timestamp": 1646986082.530837
  },
  "2": {
    "file": "probefile.txt",
    "folder": "archivos/hello/2",
    "time": "09:13:55 11/03/2022",
    "timestamp": 1646986435.9004476
  },
  "3": {
    "file": "probefile.txt",
    "folder": "archivos/hello/3",
    "time": "09:13:56 11/03/2022",
    "timestamp": 1646986436.6196616
  },
  "4": {
    "file": "probefile.txt",
    "folder": "archivos/hello/4",
    "time": "09:13:57 11/03/2022",
    "timestamp": 1646986437.987895
  }
}
```
Y éste el de `.default`

```json
4
```

### `remove_file`

Para borrar un archivo, el comando es el siguiente:

```commandline
curl -X DELETE http://localhost:5000/remove/<etiqueta>
```
Que borra el último archivo subido. Si se quiere borrar alguna versión en concreto:
```commandline
curl -X DELETE http://localhost:5000/remove/<etiqueta>:<version>
```

Ejemplos:

```commandline
curl -X DELETE http://localhost:5000/remove/hello
curl -X DELETE http://localhost:5000/remove/hello:default
curl -X DELETE http://localhost:5000/remove/hello:2
```

En este caso, indicar la versión es totalmente opcional.
Las dos primeras sentencias, que contienen las etiquetas _hello_ y _hello:default_ tienen el mismo efecto: borrar el último archivo subido.
La otra sentencia, que contiene la etiqueta _hello:2_ elimina la versión _2_ del archivo asignado a la etiqueta _hello_.

En los 3 casos, el archivo `.history` se actualiza con la eliminación de la información al correspondiente archivo.

#### TODO

* _Implementar un método para listar los archivos. Posiblemente 2 métodos distintos:_
    1. _Uno que liste los elementos asignados a la versión `default` de todas las etiquetas._
    2. _Uno que liste todos los elementos de una etiqueta en concreto._
* _Actualmente `remove_file` si borra todos los elementos de una etiqueta, deja la carpeta de esa etiqueta y los archivos `.history` y `.default`. Solucionar esto._
* _Implementar `buffetStorage`, un contenedor que contenga todos los archivos, pero que deje abierto a los modelhost el correspondiente a la versión `default`._
* _Unificar BuffetVC con MLBUFFET_
