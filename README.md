# Trading

## Ideas del Usuario

Bueno, pero antes de hacer el script quiero que nos pongamos de acuerdo con algun plan.
Quiero que veas todo lo que tengo anotado.
Como prefacio me parece que lo que estamos inventando es un bot que intente predecir la psicologia humana de prediccion de compra-venta de acciones. Y siento que lo que tenemos que entender es la cabeza de un inversor antes, despues y durante el momento de comprar algun tipo de accion.
Siento que un inversor no solo ve el grafico y tambien ve distintas cosas. Por eso creo que las cosas que tiene que ser capaz de relacionar la IA. (Partiendo de que yo como creador aun no tengo ninguna de esta informacion)
Sea:
Quiero que tenga acceso a noticias de ultimo momento. No importa la tardanza en la que le llega la noticia.
Siento que las noticias deben dividirse en grados 
1er grado, 2do grado, 3er grado. Es decir en base al nivel de relevancia. He leido diarios randoms que parecen hablar de una empresa como que va a pegar el boost del año y o ya lo pego o simplemente el diario esta siendo muy amarillista con una noticia y sus implicaciones reales en la empresa.
A medida que las noticias se acercan a 1er grado tienen mas efecto en el efecto real que tienen en el valor de la empresa y a medida que se acercan a 3er grado estan mas relacionadas con el sentimiento que hay sobre esa empresa. Que influye supongo en cierto modo en la volatilidad. Y en la capacidad de cambio de maximos y minimos y muy al final de la linea en el valor de la empresa con respecto al tiempo que creo que es lo interesante.
Creo que la IA debe tener acceso a datos historicos del valor con respecto de la empresa hasta el los minutos para que el bot entienda como fluctua el mercado, eso es un punto del prefacio. El bot tiene que tener una idea de como fluctua en general.
El bot tiene que tener en cuenta como dijimos antes las opiniones, el sentimiento en general de las posibilidades de la empresa. Poder poner en una linea del tiempo ese sentimiento (es decir cuando da frutos ese presagio del conocimiento) y evaluar con respecto al pasado si ese presentimiento dio frutos. Hay que tener en cuenta lo misleading que puede ser dicha informacion y agarrarla muy con pinzas. Esto quizas decrece el nivel de certeza del que luego hablaremos.
Hay que tener en cuenta la macroeconomia y la microeconomia del mundo, la empresa y cosas asi. Como cadenas de suministros (Esto se hablara luego pero el punto es que una empresa tiene que repercutir en otra de cierto modo, tanto en el sentimiento como en la valoracion, del mismo modo que NVIDIA afecta al bitcoin, NVIDIA afecta a otras empresas. Ya hablare de esta red que quiero que se cree.). Tambien habria que poder relacionar el pais con la empresa, con la situacion actual del mundo, como si hay guerra o cosas asi. Obviamente es muy riesgoso invertir en petroleo si el estrecho de ormuz esta bloqueado y cosas asi.
Siguiendo con las noticas, como dije, siento que habria que mapear las noticias con el evento historico y la repercucion que tiene en el mercado. Es decir, evualuar como a medida que el tiempo transcurre afecta el impacto que tiene una noticia. Vos dijiste que apenas sale una noticia el 10% crecio al instante, pero yo creo que eso es mentira. No todo es algoritmico e instantaneo. Tambien hay grandes inversores que toman decision manualmente y obviamente el populo se va enterando de la noticia y he visto como estas noticias a pesar de no darte un 10% en un instante quizas si te pueda dar un 5% en un dia. Obviamente es una apuesta muy a corto plazo y quizas riesgosa pero de eso ya hablaremos.
Me gustaria que sumado al sentimiento se tenga una constancia de la aceptacion de la empresa esto hay que tener en cuenta por posibles regularizaciones, etica, moral, etc. Por ejemplo. Es complicado confiar tanto en una empresa de autos que no tiende a lo electrico con respecto a una que si. Porque cosas como estas pueden afectar con regulaciones en general como la Union europea y cosas asi.
Como dije antes quiero que se tenga una relacion empresa a empresa, preferentemente hay que tener una cierta calidad de la info y una idea de lo bien que relaciona esa informacion con los datos del valor de la empresa en el mercado que es nuestro pilar al que nos debemos abstener porque es como la verdad absoluta. Puede ser absurda o no. Pero es absoluta.
Quiero que, teniendo en cuenta todo eso el bot sea capaz de generar reportes.
La interfaz queda por definir y el nivel de automatizacion y alertas tambien.
Pero el punto es que me gustaria algo como
Rendimiento esperado (en porcentaje y un rango de rendimiento esperado) con respecto a una cantidad de tiempo (algo como un slider de 1 dia, una semana, 2 semanas, meses, y años, desde la hora emitida del reporte)
Unido a eso un nivel de certeza. Que relaciona claramente la posibilidad de estar en lo correcto, tambien en porcentaje. Naturalmente a medida que mas tiempo pasa, la certeza va disminuyendo, como la vida misma.
Me gustaria que haya algo medio novedoso con mucho riesgo con respecto a la posibilididad de una noticia impactante, es obviamente imposible de predicir con precision pero siento que tiene que haber una tension que se acumula, por ejemplo. Apple empieza a perder valor de empresa porque hace mucho no saca algo nuevo. Entonces quizas saquen un celu nuevo, habria que poder adelantarse a cosas asi. Para eso obviamente estan las conferencias, pero el punto es que eso va de mano con el sentimiento imagino y la especulacion, no necesariamente cierto pero informacion importante.
Por otro lado, el bot debe ser de recomendacion de trading por ahora, nada automatico.
Por otro lado, hablemos sobre el calculo de valor esperado.
La formula que vos me pasaste tiene que ver con la rentabilidad esperada del bot y yo me refiero a la rentabilidad que puede dar invertir en la empresa. Algo como expected bet value. No deja de ser una apuesta. Quizas no existe una formula tan simple para esto. Pero para eso siempre podemos ayudarnos de una IA o alguna formula matematica con heuristica en base a todo lo que vengo diciendo. Obviamente hay que tener en cuenta los costos del broker, tanto de compra como de venta. En mi caso uso IOL.
Tambien estaria bueno algo de backtesting automatico.
Supongamos que yo entreno al modelo en cierta data pasada. A medida que pasa el tiempo va generandose nueva data. No tiene sentido hacer backtesting con data que ya sucedio porque obviamente va a predecir siempre. Pero a medida que pasa el tiempo se va generando nueva data y eso creo que es importante para el crecimiento. Siento que tendria que haber una relacion para este backtesting entre lo esperando y un valor de desviacion esperada por el caos psicologico que es el mercado para definir un valor de la capacidad del bot de predicir que tiene.
Creo que eso seria todo por ahora.
Hay ideas para el futuro pero por ahora dejemoslo aca. Creo que ya es bastante trabajo y ya se que puede ser abrumador pero estamos hablando de dinero y es cosa seria.
Asi que me gustaria que definamos una estructura sobre la idea general y ordenemos un poquito todas estas cosas que quiero tener en cuenta para poder definir el algoritmo. Tambien tenemos que ver que tiene de automatico este bot. Y como hacer el servicio. Porque no creo que simplemente sea escuchar una pagina de noticias como un websocket o algo asi. Siento que tiene que ser mas inteligente. Pero esas cosas escapan de mis ideas. En cierto modo tengo la nocion de un programa que se ejecuta y termina en el momento.
Asi que que opinas de todo esto.
Btw. No intentes hablarme como si no entendiera. Asume que entiendo lo que dices y caso contrario te preguntare. 


### Reporte resumido de IA, ideas ordenadas

Me parece perfecto el enfoque. Lo que estás describiendo no es un simple bot de señales, es un modelo de **finanzas conductuales (Behavioral Finance)** combinado con un **Knowledge Graph (Grafo de Conocimiento)**. Estás intentando modelar la entropía del mercado desde la psicología del rebaño y la interconectividad global.

Vamos a estructurar y ordenar todas tus notas en una arquitectura de software y de datos real.

### 1. La Ontología del Mercado (El Grafo de Relaciones)

Para lograr esa red donde "NVIDIA afecta a BTC y un bloqueo en Ormuz afecta al petróleo", una base de datos relacional (SQL) te va a quedar corta. Lo que estás definiendo es un Grafo.
Necesitas modelar esto con herramientas como Neo4j o directamente construir tensores, donde los **Nodos** son empresas, países, o materias primas, y las **Aristas (Edges)** son las relaciones ("proveedor de", "competidor de", "regulado por").

* **La tensión acumulada:** Esto en estadística se modela buscando divergencias. Si el nodo "Apple" tiene un sentimiento general que se mantiene neutro/positivo (expectativa de un nuevo producto) pero el nodo del precio lleva una tendencia bajista sostenida (mean reversion), la distancia entre ambos nodos genera ese "valor de tensión" o probabilidad de un *breakout*.
* **Regulaciones y Ética (ESG):** Actúan como pesos (weights) negativos o positivos a largo plazo sobre los nodos de ciertas empresas, afectando su volatilidad esperada.

### 2. Clasificación y Latencia de Noticias (El NLP Pipeline)

Descartamos competir en microsegundos y nos enfocamos en el *ripple effect* (el efecto dominó humano de 5% en un día).
Tu idea de los 3 grados es la base de un buen pipeline de Procesamiento de Lenguaje Natural (NLP). El bot no solo lee la noticia, la clasifica:

* **Grado 1 (Hard Facts):** Reportes de ganancias (10-K), renuncias de CEOs, cambios de tasas de la FED. Impacto directo y cuantificable en el valor intrínseco.
* **Grado 2 (Ecosistema):** Rupturas de cadena de suministro, regulaciones (Ej: Unión Europea contra el motor a combustión). Impacto a mediano plazo en el Grafo.
* **Grado 3 (Sentimiento y Ruido):** Amarillismo, artículos de opinión motivados, tweets de analistas. Afectan la volatilidad a corto plazo, no el valor fundamental.

### 3. La Matemática del Retorno Esperado (El Valor de la Apuesta)

Querías una fórmula orientada a la inversión en sí, teniendo en cuenta la estructura de costos de operar en Argentina con brokers como IOL (donde pagas comisión de compra, comisión de venta y derechos de mercado, además del spread).

Lo que buscas es el **Valor Esperado Discreto de la Operación ($E[O]$)**. La IA no te va a dar un número mágico, te va a dar una *distribución de probabilidad*.

$$E[O] = (U \cdot P_u) - (D \cdot P_d) - C_{IOL}$$

* **$U$ (Upside):** El porcentaje de subida predicho (ej. +5%).
* **$P_u$:** El nivel de certeza de la subida (ej. 65%).
* **$D$ (Downside):** La caída máxima histórica para ese tipo de setup (el riesgo real, ej. -3%).
* **$P_d$:** Probabilidad de que el escenario falle (ej. 35%).
* **$C_{IOL}$:** Sumatoria de costos fijos de entrada y salida (Comisión de IOL + Derechos de Mercado + IVA de la comisión + Costo de oportunidad/Spread).

Si $E[O] > 0$ por un margen que supere la tasa libre de riesgo, el bot genera el reporte de recomendación. El nivel de certeza ($P_u$) decae exponencialmente a medida que el horizonte de tiempo (tu slider de 1 día a 1 año) aumenta, porque en sistemas caóticos la varianza escala con el tiempo.

### 4. Backtesting Continuo (Walk-Forward Analysis)

Lo que describes ("no tiene sentido entrenar con data pasada y testear con data que ya sucedió") es el estándar de oro para evitar modelos sobreajustados. En la industria, esto se llama **Walk-Forward Optimization** o *Paper Trading* continuo.
El modelo se entrena hasta el día $T$. A partir de $T+1$, empieza a generar predicciones sobre datos que jamás vio. Si la predicción a 1 semana falla, el bot calcula el *Error Cuadrático Medio* de su fallo, ajusta sus pesos internos, y el día $T+8$ vuelve a intentar. La "desviación por el caos psicológico" se mide calculando la entropía cruzada entre la curva de predicción de la IA y el movimiento caótico real.

### 5. Arquitectura de Ejecución (¿Cómo funciona el bot físicamente?)

Mencionaste que tenías la noción de un programa que se ejecuta y termina. Para un sistema así, esa arquitectura no sirve. Necesitas separar el sistema en microservicios o procesos concurrentes. Así es como deberías estructurarlo (idealmente en Python o incluso con partes en lenguajes más rápidos o orientados a UI si luego le haces una interfaz):

1. **Los Daemons (Workers en background):** Scripts que corren 24/7 en un servidor (o una Raspberry Pi/VPS). Uno escucha webhooks/RSS de noticias (Grados 1 a 3), otro hace llamadas a APIs de precios cada minuto, y los guardan en la base de datos (PostgreSQL + Neo4j). No analizan nada, solo recolectan y persisten datos de forma asíncrona.
2. **El Motor de Inferencia (El Cerebro):** Un proceso programado (un *cronjob* o un *scheduler*) que se despierta cada X minutos. Toma los datos nuevos, actualiza los grafos, corre los modelos de NLP para el sentimiento y actualiza la tabla de predicciones.
3. **El Frontend / Generador de Reportes:** Cuando tú abres la interfaz (sea una consola o una web app local), el sistema no calcula nada desde cero. Simplemente consulta a la base de datos el último estado del "Cerebro" y te renderiza la interfaz con el *slider* de tiempo y los porcentajes de certeza.

Tienes la abstracción del sistema perfectamente delineada en tu cabeza. El desafío ahora es puramente de ingeniería de datos: ¿Qué construimos primero? Recomiendo no tocar un solo modelo de IA hasta no tener la base de datos ingiriendo información limpia y continua.

### Pregunta: ¿Cuál debe ser el comportamiento esperado de la aplicación cuando el servicio se pausa y se reanuda?

Respuesta: Dado que el sistema opera en una notebook sin un 100% de uptime (sujeta a suspensiones, reinicios o cortes de internet), el bot debe diseñarse bajo principios de tolerancia a fallos, asincronía y recuperación de estado (catch-up). El comportamiento esperado al reanudarse se define en cuatro pilares:
Idempotencia en la Ingesta: El sistema debe poder ejecutarse múltiples veces sobre el mismo rango de tiempo sin duplicar registros. Esto ya está parcialmente resuelto: al usar hashes MD5 de las URLs como clave primaria en SQLite, si el bot se apaga a mitad de una descarga, al reiniciarse simplemente ignorará lo ya guardado (IntegrityError) y continuará con lo nuevo.
Relleno de Huecos (Gap Filling): Al despertar, el bot debe consultar en la base de datos el timestamp del último registro exitoso. Luego, debe solicitar a la API (tanto de noticias como de precios) el rango de datos desde ese último timestamp hasta el momento actual datetime.now(), rellenando el "agujero" de tiempo en el que estuvo inactivo.
Reconciliación de Estado con el Broker: El bot nunca debe confiar ciegamente en su estado local sobre las posiciones abiertas. Al reanudarse, el primer paso del módulo de ejecución debe ser un ping a la API del broker (ej. Interactive Brokers, Alpaca, Binance) para sincronizar el portafolio real, verificar si alguna orden límite se ejecutó mientras estaba dormido y ajustar sus variables internas en consecuencia.
Cierre Elegante (Graceful Shutdown): Para evitar corrupción en SQLite al suspender la notebook, el código principal deberá capturar señales del sistema operativo (como SIGINT o SIGTERM) para hacer un conn.commit() y cerrar las conexiones a la base de datos antes de que el proceso sea liquidado.


### Anexo Técnico: Matemática del "Cerebro Híbrido" y Valor Esperado ($E[O]$)

Para predecir la psicología humana y el retorno esperado, el sistema abandona los promedios estadísticos rígidos y adopta un modelo de *Machine Learning* predictivo. La IA no evalúa eventos aislados, sino que procesa el estado completo del mercado en un instante dado mediante vectores de características.

#### 1. El Vector de Estado del Mercado ($\vec{X}$)

Cada vez que ingresa una noticia, el sistema construye un vector $\vec{X}$ que captura tanto la semántica como la estructura algorítmica del activo. Este vector será el *input* de la red neuronal:

$$\vec{X} = \begin{bmatrix} I \\ S \\ M_{24h} \\ \text{RSI} \\ \sigma_{atr} \\ G_{shock} \end{bmatrix}$$

Donde:

* $I$: Importancia de la noticia, evaluada en un espectro continuo $[0.0, 1.0]$.
* $S$: Sentimiento de la noticia extraído por FinBERT $[-1.0, 1.0]$.
* $M_{24h}$: Momentum del precio (aceleración de la tendencia previa).
* $\text{RSI}$: Índice de saturación $[0, 100]$ para detectar si el inversor está eufórico o en pánico.
* $\sigma_{atr}$: Volatilidad intrínseca actual (Average True Range).
* $G_{shock}$: El valor de impacto sistémico propagado por el Grafo Semántico.

#### 2. La Matemática del Grafo Semántico (NetworkX)

El mercado es una red de nodos conectados por verbos (aristas). No dependemos de menciones casuales; las empresas se vinculan mediante relaciones con pesos definidos $\vec{W}$ (ej. "adquiere" $= 0.9$, "provee" $= 0.6$, "compite" $= -0.5$).

El contagio que recibe una empresa $A$ desde sus vecinos se calcula mediante el producto escalar entre el vector de pesos de las relaciones $\vec{W}$ y el vector de los shocks iniciales de los vecinos $\vec{S}$. Utilizando la notación de producto escalar, esto se define como:

$$G_{shock} = \vec{W} \times \vec{S} = \sum_{i=1}^{n} w_i s_i$$

Esto permite modelar cadenas de suministro y repercusiones sistémicas de forma matemáticamente estricta.

#### 3. Predicción Probabilística (El Modelo de ML)

A diferencia de un algoritmo tradicional que predice un único número, nuestra IA funciona como un modelo probabilístico. Para un horizonte de tiempo determinado $t$ (el *slider* de la interfaz), la red neuronal mapea el vector de entrada $\vec{X}$ a los parámetros de una distribución normal de retornos esperados:

$$f(\vec{X}, t) = (\mu_t, \sigma_t)$$

* $\mu_t$: El rendimiento porcentual medio esperado para el tiempo $t$.
* $\sigma_t$: La desviación estándar (la incertidumbre o "caos psicológico" proyectado por el modelo).



#### 4. Certeza, Tiempo y Valor de la Apuesta ($E[O]$)

En la vida real y en los sistemas caóticos, la varianza escala con la raíz cuadrada del tiempo ($\sqrt{t}$). Por lo tanto, la certeza de la IA decrece naturalmente a medida que el horizonte de inversión se amplía.

La Certeza ($C_t$) se define como la probabilidad matemática de que el rendimiento real supere los costos de transacción ($c$) del broker:

$$C_t = P(R > c) = 1 - \Phi\left(\frac{c - \mu_t}{\sigma_t \sqrt{t}}\right)$$


*(Donde $\Phi$ es la función de distribución acumulada normal).*

Finalmente, el **Valor Esperado Discreto de la Operación** (nuestra rentabilidad apostada) se calcula ponderando el escenario de éxito y el de fracaso:

$$E[O]_t = \left( \mu_t^+ \cdot C_t \right) - \left( \vert{}\mu_t^-\vert{} \cdot (1 - C_t) \right) - c$$

Si $E[O]_t > 0$, el bot levanta la señal de recomendación.
