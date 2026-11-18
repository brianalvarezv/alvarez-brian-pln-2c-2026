# RAG local para empleados de comercio

Sistema de consulta de normativa relacionada con los empleados de
comercio. La aplicación utiliza un enfoque **RAG (Retrieval-Augmented
Generation)**: primero recupera fragmentos de los documentos del corpus
y luego utiliza un modelo de lenguaje local para elaborar una respuesta
a partir de ese contexto.

La interfaz permite ingresar una pregunta y visualizar por separado la
respuesta generada y los fragmentos recuperados que fueron enviados al
modelo.

## 1. Objetivo y alcance

Nuestro objetivo es que los trabajadores mercantiles de la rama general en Argentina puedan consultar información contenida en documentos normativos vinculados con su actividad, para otorgarles herramientas que los apoyen en el conocimiento de sus derechos. Se trata de uno de los gremios con mayor cantidad de afiliados en el país.

El sistema no realiza una búsqueda general en Internet ni consulta una
base legal externa: sus respuestas se generan utilizando los fragmentos
recuperados del corpus local configurado en el proyecto. Por eso, el
alcance de las respuestas depende de los documentos incorporados y de la
recuperación realizada.

## 2. Corpus documental

La aplicación carga los siguientes tres archivos PDF desde la carpeta
`datos/`:

  ----------------------------------------------------------------------------
  Archivo                                  Contenido / referencia
  ----------------------------------------------------------------------------
  `cct130_75.pdf`                          Convenio Colectivo de Trabajo
                                           130/75.


  `Ley20744_legales.pdf`                   Ley de Contrato de Trabajo 20.744.

  `Ley23551_Asociaciones_Sindicales.pdf`   Ley 23.551 de Asociaciones
                                           Sindicales.
  ----------------------------------------------------------------------------

Los archivos deben conservar esos nombres y ubicarse dentro de `datos/`,
porque `app.py` utiliza esas rutas para cargarlos.

> **Procedencia y condiciones de uso:** Dado que se trata de normativa vigente en el país, los documentos son de libre acceso. Sin embargo, ponemos a disposición una copia de cada uno. En cuanto al origen de ellos, es el siguiente:

- Convención colectiva del trabajo 130/75, Disponible en la web de FAECYS https://www.faecys.org.ar/convencion-colectiva-de-trabajo-no-13075/. En el archivo PRUEBAS.md se testea el documento con la pregunta "¿Cuánto tiempo de descanso tienen los trabajadores durante la jornada?".

- Ley 20744 de contratos de trabajo. Disponible en la web de FAECYS https://www.faecys.org.ar/ley-20-744-contrato-de-trabajo/. En el archivo PRUEBAS.md se testea el documento con la pregunta "¿Cómo define el contrato de trabajo el artículo 21 de la LCT?"

- Ley 23551 de asociaciones sindicales. Disponible en la web de FAECYS https://www.faecys.org.ar/ley-23-551-asociaciones-sindicales/. En el archivo PRUEBAS.md se testea el documento con la pregunta "¿Qué derechos sindicales enumera el artículo 4 de la Ley 23551?"

Al día 17 de noviembre de 2026, los tres documentos se encuentran disponibles.

## 3. Arquitectura y funcionamiento

El flujo general del sistema es el siguiente:

``` text
Archivos PDF en datos/
        |
        v
Carga de documentos y extracción de texto
        |
        v
Fragmentación del contenido
        |
        v
Generación de embeddings con Ollama (bge-m3)
        |
        v
Almacenamiento y búsqueda en Chroma
        |
        v
Pregunta del usuario
        |
        v
Recuperación de los fragmentos más similares
        |
        v
Construcción del contexto con archivo y página
        |
        v
Generación de respuesta con Ollama (granite4:latest)
        |
        v
Gradio: respuesta y fragmentos recuperados
```

### 3.1. Carga de documentos

La función `cargar_documentos()` lee los PDF indicados en el código
mediante `PyPDFLoader`. El contenido se incorpora como documentos de
LangChain y conserva los metadatos de origen y página que proporciona el
cargador.

### 3.2. Fragmentación

El texto extraído se divide mediante `RecursiveCharacterTextSplitter`,
con estos parámetros:

  Parámetro           Valor
  ----------------- -------
  `chunk_size`          300
  `chunk_overlap`        80

El solapamiento permite conservar parte del contexto entre fragmentos
consecutivos. Hicimos pruebas con 300 ya que los artículos de estas normativas son cortos, bajar más de ahí sería forzar cortes en la evidencia. Luego contrastamos con pruebas de chunk size mayores, que no dieron mejores resultados, y demoraban los tiempos de la respuesta.

### 3.3. Embeddings e índice vectorial

Los fragmentos se representan mediante embeddings generados localmente
con el modelo `bge-m3`, a través de Ollama.

Los vectores y documentos se almacenan en una base Chroma en la carpeta
local:

``` text
chroma_db_bge_m3/
```

La aplicación agrega los fragmentos en lotes de 10. Si la colección ya
contiene registros, reutiliza el índice existente y no vuelve a cargar
ni a incorporar los mismos documentos al iniciar la interfaz. Se resolvió lotear los fragmentos por sugerencia del asistente de IA, ya que el procesamiento del conjunto completo se hacía imposible para el hardware disponible. 

### 3.4. Recuperación y generación

Al recibir una pregunta, el sistema realiza una búsqueda por similitud
en Chroma y recupera los **5 fragmentos** más similares (`k=5`).

Con esos fragmentos construye el contexto que recibe el modelo generador
`granite4:latest`, ejecutado localmente mediante Ollama. El prompt
indica que la respuesta debe basarse únicamente en el contexto
proporcionado y establece un mensaje específico cuando la información
solicitada no aparece allí.

La aplicación también prepara una salida con el nombre del archivo, el
número de página cuando está disponible, la distancia devuelta por la
búsqueda y el texto de cada fragmento recuperado.

La distancia es un dato para inspeccionar el resultado de la búsqueda;
no representa una probabilidad de que la respuesta sea verdadera. Que un
fragmento haya sido recuperado tampoco garantiza que el modelo lo haya
interpretado correctamente. Por esto, decidimos elegir el número k que mejor equilibraba la disponibilidad de contexto; la variedad de fragmentos disponibles en el corpus respecto de cada pregunta (por ejemplo, al preguntar por los trabajadores, muchos fragmentos pueden ser convocados) y la redundancia, ya que si bien un k=15 no arrojó resultados irrelevantes o insólitos, tampoco agregó información sustancial a las respuestas.

## 4. Tecnologías utilizadas

  -----------------------------------------------------------------------
  Tecnología / biblioteca             Función
  ----------------------------------- -----------------------------------
  Python 3.12                         Lenguaje y entorno de ejecución.

  `uv`                                Creación del entorno virtual e
                                      instalación de dependencias.

  Ollama                              Ejecución local de los modelos.

  `bge-m3`                            Modelo utilizado para generar
                                      embeddings.

  `granite4:latest`                   Modelo utilizado para generar las
                                      respuestas.

  LangChain                           Integración de carga,
                                      fragmentación, embeddings y
                                      generación.

  `PyPDFLoader`                       Extracción del contenido de los
                                      PDF.

  `RecursiveCharacterTextSplitter`    División del texto en fragmentos.

  Chroma (`langchain-chroma`)         Almacenamiento y recuperación
                                      vectorial.

  Gradio                              Interfaz local para realizar
                                      consultas y visualizar resultados.

  `python-dotenv`                     Lectura de variables de
                                      configuración desde `.env`.
  -----------------------------------------------------------------------

## 5. Requisitos previos

Antes de ejecutar el proyecto se necesita:


-   Python **3.12**.
-   `uv` instalado.
-   Ollama instalado y en ejecución.
-   Los documentos PDF dentro de `datos/`.
-   Los modelos `granite4:latest` y `bge-m3` descargados en Ollama.

La descarga de los modelos requiere conexión a Internet. Una vez
descargados, se ejecutan localmente mediante Ollama.

Primero instale [Ollama](https://ollama.com) y descargue los dos modelos.

```powershell
ollama pull granite4:latest
ollama pull bge-m3
```
Luego debe instalar `uv` en PowerShell con el comando `-ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

En VS Code elija el kernel de `.venv`. Compruebe con el comando `ollama list` que los modelos necesarios estén presentes.

## 6. Instalación y preparación del entorno

Los siguientes comandos están escritos para una terminal de Windows,
ubicada en la carpeta raíz del proyecto, donde clonó este repositorio.

### 6.1. Crear el entorno virtual

``` powershell
uv venv --python 3.12
```

### 6.2. Activar el entorno virtual

En PowerShell:

``` powershell
.venv\Scripts\Activate.ps1
```

Si se utiliza el símbolo del sistema (CMD):

``` cmd
.venv\Scripts\activate.bat
```

### 6.3. Instalar las dependencias

Con el entorno activado, ejecutar:

``` powershell
uv pip install -r requirements.txt
```

El archivo `requirements.txt` debe incluir las dependencias utilizadas
por la aplicación:

- `ollama`>=0.6
- `langchain-core`>=1.0
- `langchain-community`>=0.4
- `langchain-text-splitters`>=1.0
- `langchain-chroma`>=1.0
- `langchain-ollama`>=1.0
- `chromadb`>=1.0
- `pypdf`>=5.0
- `pandas`>=2.2
- `matplotlib`>=3.9
- `gradio`>=5.0
- `google-search-results`>=2.4
- `python-dotenv`>=1.0
- `ipykernel`>=6.29


## 7. Instalación y descarga de modelos con Ollama

Si ya instaló Ollama y descargó los modelos siguiendo los pasos anteriores, solo le queda verificar que estén descargados.

Para comprobarlo, escriba:

``` powershell
ollama list
```

La aplicación utiliza `granite4:latest` para generar respuestas y
`bge-m3` para crear los embeddings y realizar las consultas vectoriales.

## 8. Configuración

La aplicación carga un archivo `.env` ubicado en la carpeta raíz del
proyecto. Si no se definen variables, utiliza estos valores
predeterminados:

  Variable                   Valor predeterminado   Uso
  -------------------------- ---------------------- ---------------------------------
  `OLLAMA_MODEL`             `granite4:latest`      Modelo generador de respuestas.
  `OLLAMA_EMBEDDING_MODEL`   `bge-m3`               Modelo de embeddings.

De manera opcional, se puede crear un archivo `.env` en la raíz:

``` dotenv
OLLAMA_MODEL=granite4:latest
OLLAMA_EMBEDDING_MODEL=bge-m3
```

Como ya se mencionó, los modelos configurados deben estar descargados en Ollama. 

## 9. Creación y reconstrucción del índice

La preparación del índice se ejecuta automáticamente al iniciar
`app.py`. Primero abrimos la terminal en la carpeta del proyecto, allí activamos el entorno virtual y entonces ejecutamos `app.py`

En el primer inicio, si la colección está vacía, la aplicación:

1.  Carga los PDF de `datos/`.
2.  Divide el contenido en fragmentos de 300 caracteres, con un
    solapamiento de 80.
3.  Genera embeddings con `bge-m3`.
4.  Incorpora los fragmentos a Chroma en lotes de 10.
5.  Guarda el índice en `chroma_db_bge_m3/`.

En los inicios siguientes, si la colección ya contiene registros, la
aplicación reutiliza el índice y omite la carga y la fragmentación.

**Importante:** el programa no comprueba si los PDF cambiaron ni
actualiza automáticamente los fragmentos existentes. Si se modifica el
corpus, el tamaño o solapamiento de los fragmentos, o el modelo de
embeddings, hay que reconstruir el índice.

Para forzar la reconstrucción, cerrar la aplicación y eliminar la
carpeta local `chroma_db_bge_m3/`. Luego, al iniciar nuevamente
`app.py`, se volverán a cargar los documentos y se generará el índice. Otra opción es utilizar la aplicación eliminar_indice.py, ubicada en la carpeta /utils.



## 10. Ejecución de la aplicación

Con Ollama en ejecución, los modelos descargados y el entorno virtual
activado, ubicarse en la carpeta raíz del proyecto y ejecutar:

``` powershell
python app.py
```

La aplicación prepara o reutiliza el índice y luego inicia la interfaz
Gradio en el navegador.

La interfaz contiene:

-   **Pregunta sobre los documentos:** campo para ingresar la consulta.
-   **Respuesta:** texto generado por el modelo.
-   **Fragmentos recuperados y enviados al modelo:** muestra el
    contenido utilizado como contexto, junto con el archivo, la página
    cuando corresponde y la distancia de recuperación.

Para finalizar la aplicación, detener el proceso desde la terminal con
`Ctrl + C`.

## 11. Estructura del proyecto

La estructura del proyecto es:

``` text
proyecto/
│
├── app.py
├── requirements.txt
├── .env                  
├── .gitignore
│
├── datos/
│   ├── cct130_75.pdf
│   ├── Ley20744_legales.pdf
│   └── Ley23551_Asociaciones_Sindicales.pdf
│
└── chroma_db_bge_m3/     # Se genera al crear el índice; no publicar
```

La carpeta `.venv/` también se genera localmente al preparar el entorno
y no debe incluirse en el repositorio.


## 12. Decisiones técnicas y límites

-   **Fragmentación:** se utilizan fragmentos de 300 caracteres con 80
    caracteres de solapamiento. Se decidió la configuración óptima dentro de las posibilidades del hardware disponible. 
-   **Cantidad recuperada:** se recuperan los 5 fragmentos más similares
    a la consulta. Como se comentó más arriba, usar menos fragmentos sería desperdiciar la multiplicidad de fuentes de respuesta dentro del corpus, y usar muchos más no produjo una mejora.
-   **Modelos:** se utiliza `bge-m3` tanto para indexar como para
    generar el embedding de la pregunta, y `granite4:latest` para
    redactar la respuesta. Esto responde a una limitación en nuestro conocimiento y al cumplimiento de una consigna académica, queda por ver si otros modelos resultan más provechosos.
-   **Fuentes y alcance de las citas:** la interfaz muestra los fragmentos efectivamente
    recuperados y enviados al generador. Esto permite inspeccionar el
    contexto, aunque no garantiza que la respuesta sea correcta. En las pruebas realizadas, las citas guardaban similitud semántica con la pregunta, y nunca vinieron vacías. Sin embargo, hubo una pregunta que no se pudo resolver aun ajustando hiperparámetros.
-   **Abstención:** el prompt solicita una respuesta específica cuando
    el contexto no contiene el dato. Esto no garantiza que el modelo
    siempre detecte correctamente la falta de información. En las pruebas, la abstención del modelo pareció precisa.

## 13. Pruebas y uso de inteligencia artificial

Los casos de prueba, las preguntas respondibles y no respondibles, los
resultados observados y la limitación identificada se documentan en un
archivo Markdown separado: **`PRUEBAS.md`**.

> **Declaración de uso de IA:** en el desarrollo de este sistema, se utilizó un asistente de IA generativa para estructurar el texto en formato Markdown, corregir errores gramaticales o dificultades de expresión, y resolver un problema específico relacionado con la fragmentación por lotes, con el que me topé debido al hardware disponible. Me refiero a la función preparar_indice que se ubica dentro del archivo app.py. Además, le pedí ayuda para armar la sintaxis de la función que elimina los índices creados automáticamente, de forma que no me demorara en la documentación de Chroma y pudiera dedicarme a las pruebas que estaba realizando. Por supuesto, todo aporte de la IA fue leído, retocado y probado por mí.
