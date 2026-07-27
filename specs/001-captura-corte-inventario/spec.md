# Feature Specification: Captura de Archivo de Corte y Control de Inventario

**Feature Branch**: `001-captura-corte-inventario`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Generá el spec a partir de @PRD.md" — PRD-001: DyP LaserCore, sistema de
automatización de captura de datos técnicos para la optimización integral del inventario y el flujo
productivo de una empresa de procesamiento de chapas metálicas.

## Clarifications

### Session 2026-07-21

- Q: Cuando una búsqueda de coincidencia por dimensiones (Oficina/Taller) encuentra más de un
  producto dentro del margen de tolerancia configurado, ¿qué criterio determinístico usa el
  sistema para elegir uno? → A: Coincidencia más cercana — se elige el producto con la menor
  diferencia de dimensiones (largo + ancho) respecto al valor buscado.
- Q: Si dos usuarios operan simultáneamente sobre el mismo producto (ej. dos órdenes de Oficina
  comprometen stock del mismo producto al mismo tiempo, o Oficina y Taller lo tocan a la vez),
  ¿cómo debe comportarse el sistema? → A: Última escritura gana — cada operación aplica su propio
  incremento/decremento sobre el valor más reciente en base de datos (suma/resta atómica), sin
  bloqueos ni reintentos; ninguna operación pisa el cambio de la otra porque ambas se aplican como
  delta, no como reemplazo de valor.
- Q: El escaneo de órdenes en Taller (Historia 3) ¿debe funcionar sin conexión a internet/red
  local, o puede asumir que el dispositivo siempre tiene conectividad al servidor? → A: Requiere
  conexión siempre — si no hay conexión, el sistema muestra un error claro y no permite escanear
  ni cerrar órdenes hasta reconectar; no hay modo offline ni sincronización posterior.

### Session 2026-07-22

- Q: ¿Qué regla de composición de contraseña debe exigir el sistema al autorregistrarse (FR-003)?
  → A: Mínimo 8 caracteres, sin otro requisito de composición (sin exigir mayúscula, número o
  símbolo).
- Q: ¿Qué formato exacto debe tener el código NEST generado al confirmar una orden (FR-012)? → A:
  Prefijo fijo `NEST-` + número secuencial con padding a 6 dígitos (ej. `NEST-000001`).
- Q: ¿Qué límites válidos debe exigir el Margen de Tolerancia Dimensional al guardarse (FR-029)? →
  A: Solo exigir que sea mayor a 0, sin límite superior explícito.
- Q: ¿Debe el sistema bloquear una cuenta o aplicar rate limiting tras intentos fallidos repetidos
  de login (FR-001)? → A: No — sin mecanismo de bloqueo ni rate limiting; cada intento fallido
  simplemente responde 401.
- Q: ¿Existe un límite de tamaño máximo para el archivo PDF subido (FR-007), más allá de la
  validación de extensión? → A: Sí, 20 MB máximo.
- Q: ¿Qué representa exactamente "multiplicidad" y cómo determina la cantidad de stock
  comprometido (FR-014)? → A: Es la cantidad de chapas físicas consumidas por la orden; el stock
  comprometido/descontado del producto de chapa es igual a la multiplicidad (multiplicidad × 1
  chapa por unidad de stock).
- Q: Si el usuario confirma la creación automática de un producto (FR-015) y esa creación falla,
  ¿qué ocurre con la confirmación de la orden en curso? → A: Todo-o-nada — la confirmación completa
  de la orden se revierte (nada se persiste) y el usuario reintenta desde la propuesta ya revisada.
- Q: ¿Qué criterio objetivo debe cumplir el "indicador visual de alerta" de stock bajo (FR-016)? →
  A: Badge/ícono de alerta junto al valor de stock, mostrado únicamente en el listado de productos
  del módulo de Inventario (no en el listado/confirmación de órdenes).
- Q: ¿Cómo se mide el 98% de acierto de extracción de SC-001 — por documento completo o por
  campo individual? → A: Por campo individual (datos generales + piezas + recortes), sobre una
  muestra de PDFs de `Archivos de Corte/`.
- Q: ¿El requisito de "conectividad activa siempre" (FR-021) es exclusivo de Taller o aplica por
  igual a Oficina/Inventario/Configuración? → A: Aplica por igual a todos los módulos — no hay modo
  offline en ninguna parte del sistema; FR-021 solo lo hace explícito para Taller porque es el
  único módulo con contexto de hardware distinto (dispositivo móvil/tablet con cámara).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acceso seguro al sistema (Priority: P1)

Un empleado de la empresa necesita iniciar sesión con su email y contraseña para acceder a
cualquier funcionalidad del sistema (Oficina, Taller, Inventario, Configuración). Si todavía no
tiene cuenta, puede crear una de forma simple. Todos los usuarios autenticados tienen el mismo
nivel de acceso a todos los módulos, ya que el sistema no distingue roles ni permisos.

**Why this priority**: Es la puerta de entrada obligatoria a todo el sistema; sin autenticación
funcionando ninguna otra historia de usuario puede probarse ni entregarse de forma realista.

**Independent Test**: Puede probarse por completo de forma aislada: crear una cuenta nueva,
cerrar sesión, iniciar sesión con esas credenciales, verificar que las rutas del sistema quedan
bloqueadas para un usuario no autenticado y accesibles para uno autenticado.

**Acceptance Scenarios**:

1. **Given** un usuario sin sesión iniciada, **When** accede a la URL del sistema, **Then** el
   sistema muestra la pantalla de inicio de sesión solicitando email y contraseña.
2. **Given** un usuario no autenticado, **When** intenta acceder a cualquier página del sistema,
   **Then** el sistema lo redirige a la pantalla de inicio de sesión.
3. **Given** un usuario que quiere registrarse, **When** ingresa un email no registrado
   previamente junto con una contraseña válida y confirma, **Then** el sistema crea la cuenta
   exitosamente.
4. **Given** un usuario que quiere registrarse, **When** el email ingresado ya pertenece a un
   usuario existente, **Then** el sistema informa el error y rechaza el alta.
5. **Given** un usuario autenticado, **When** accede a cualquier módulo del sistema (Oficina,
   Taller, Inventario, Configuración), **Then** el sistema concede el acceso sin restricciones
   adicionales de rol o permiso.
6. **Given** un usuario autenticado, **When** selecciona la acción de cerrar sesión, **Then** el
   sistema descarta el token de sesión y lo redirige a la pantalla de inicio de sesión, bloqueando
   el acceso a los módulos hasta que vuelva a autenticarse.

---

### User Story 2 - Captura del archivo de corte y generación de orden de trabajo (Priority: P2)

Un empleado de Oficina sube el archivo de corte en PDF generado por el software de la máquina de
corte láser. El sistema extrae automáticamente los datos generales, el listado de piezas y los
recortes sobrantes, y se los presenta al usuario para que los revise, corrija si hace falta, y
confirme. Al confirmar, el sistema genera un código NEST único, guarda la orden de trabajo,
compromete el stock de chapa correspondiente en el inventario e imprime la orden con su código de
barras.

**Why this priority**: Es el valor central del producto — reemplaza la codificación y carga
manual, principal fuente de errores actual en el inventario. Sin esta historia el sistema no
resuelve el problema que motiva el proyecto.

**Independent Test**: Puede probarse de punta a punta subiendo un PDF de ejemplo del archivo de
corte, validando los datos extraídos en pantalla, confirmando la orden y verificando que se generó
un código NEST, que la orden quedó en estado "vigente" y que el stock del producto correspondiente
se comprometió según la multiplicidad indicada.

**Acceptance Scenarios**:

1. **Given** un archivo con extensión PDF válido, **When** el usuario lo sube al sistema, **Then**
   el sistema acepta la carga.
2. **Given** un archivo con una extensión distinta a PDF (ej. .xlsx o .jpg), **When** el usuario
   intenta subirlo, **Then** el sistema rechaza la carga y muestra un mensaje de error indicando
   que solo se admiten archivos PDF.
3. **Given** un archivo PDF de corte con multiplicidad, dimensiones, espesor, material y tiempo de
   ejecución estimado, **When** el usuario lo sube al sistema, **Then** el sistema extrae y
   muestra esos valores en los campos correspondientes para su validación, sin persistirlos
   todavía.
4. **Given** un archivo PDF de corte con un listado de piezas (descripción y cantidad por ítem),
   **When** el usuario lo sube, **Then** el sistema extrae cada pieza junto con su cantidad
   correspondiente.
5. **Given** un ítem del listado de piezas identificado como recorte sobrante (descripción "Saved
   scrap") con sus dimensiones codificadas en el nombre técnico del ítem (ej. "800x400"), **When**
   el sistema procesa el archivo, **Then** extrae el largo y el ancho del recorte a partir de ese
   nombre técnico.
6. **Given** datos extraídos mostrados en pantalla, **When** el usuario detecta un valor incorrecto
   y lo corrige antes de confirmar, **Then** el sistema utiliza el valor corregido por el usuario y
   no el originalmente extraído.
7. **Given** la confirmación de los datos por parte del usuario, **When** confirma la creación de
   la orden, **Then** el sistema genera un código NEST único y secuencial y lo asigna a la nueva
   orden de trabajo, guardándola con estado "vigente".
8. **Given** una orden de trabajo guardada, **When** se confirma la orden, **Then** el sistema
   imprime un documento con el código de barras del código NEST y el detalle de piezas, y ese
   código de barras es decodificable por un lector estándar a resolución de impresión típica.
9. **Given** la confirmación de la orden, **When** el sistema identifica el producto
   correspondiente (material, espesor y dimensiones dentro del margen de tolerancia configurado)
   en el maestro, **Then** compromete automáticamente el stock de chapa según la multiplicidad
   indicada.
10. **Given** la confirmación de la orden, **When** el producto no existe en el maestro, **Then**
    el sistema advierte al usuario de la ausencia del producto.
11. **Given** la advertencia de producto inexistente, **When** el usuario confirma la creación
    automática, **Then** el sistema crea el ítem con los datos técnicos extraídos del PDF y stock
    físico en cero.
12. **Given** un producto cuyo stock disponible (stock físico menos stock comprometido) alcanza o
    cae por debajo de su punto de pedido tras comprometer la orden, **When** se genera la orden,
    **Then** el sistema muestra un indicador visual de alerta, sin bloquear el proceso.
13. **Given** un listado de órdenes de trabajo, **When** el usuario filtra por estado
    ("vigente"/"cerrada") y/o busca por código NEST (coincidencia parcial), **Then** el sistema
    muestra únicamente las órdenes que cumplen los criterios combinados; sin ningún filtro
    seleccionado, muestra todas las órdenes.

---

### User Story 3 - Cierre de la orden en taller y descuento de stock (Priority: P3)

Un operario de Taller recibe la orden de trabajo impresa, escanea su código de barras (o ingresa
el código NEST manualmente) para ubicarla en el sistema, y la finaliza al terminar el corte. Al
finalizar, el sistema descuenta el stock físico y comprometido según la multiplicidad, y da de
alta o incrementa en el inventario los recortes sobrantes detallados en la orden.

**Why this priority**: Cierra el ciclo de control de stock iniciado en Oficina; sin esta historia
el stock queda comprometido pero nunca se refleja el consumo real ni el ingreso de recortes.

**Independent Test**: Puede probarse de forma aislada partiendo de una orden "vigente" ya
existente: escanear o ingresar su código NEST, verificar que se muestra la orden correcta,
finalizarla y comprobar que el stock físico/comprometido del producto se descontó y que los
recortes declarados quedaron reflejados en el maestro de productos.

**Acceptance Scenarios**:

1. **Given** una orden de trabajo entregada al taller, **When** el usuario escanea su código de
   barras NEST, **Then** el sistema muestra en pantalla la orden asociada.
2. **Given** un usuario que no puede o prefiere no escanear, **When** ingresa el código NEST
   manualmente y confirma, **Then** el sistema busca y muestra la orden asociada, igual que si la
   hubiera escaneado.
3. **Given** una orden en estado "vigente", **When** el usuario confirma la finalización desde la
   pantalla de taller, **Then** el estado de la orden cambia a "cerrada".
4. **Given** un escaneo exitoso, **When** el usuario finaliza el proceso de corte, **Then** el
   sistema descuenta del maestro de productos el stock comprometido y el stock físico, según la
   multiplicidad definida en la orden.
5. **Given** un sobrante de material detallado en la orden sin coincidencia de producto existente
   (mismo material, espesor y dimensiones dentro del margen de tolerancia), **When** el usuario
   finaliza el proceso de corte, **Then** el sistema da de alta el recorte como nuevo producto en
   el maestro.
6. **Given** un sobrante de material detallado en la orden que coincide con un producto existente
   (mismo material, espesor y dimensiones dentro del margen de tolerancia), **When** el usuario
   finaliza el proceso de corte, **Then** el sistema aumenta el stock de ese producto en la
   cantidad detallada.

---

### User Story 4 - Gestión manual del maestro de productos (Priority: P4)

Un empleado autenticado necesita dar de alta, editar y consultar productos (chapas y recortes) en
el maestro de inventario de forma independiente del flujo automático de Oficina/Taller, por
ejemplo para cargar stock inicial o corregir datos.

**Why this priority**: Es necesaria para poder operar el sistema desde el primer día (carga de
stock inicial) y para mantenimiento continuo, pero no es la vía principal de alta de productos una
vez que el flujo automático de Oficina/Taller está en marcha.

**Independent Test**: Puede probarse de forma aislada dando de alta un producto nuevo con datos
válidos, editando uno de sus campos permitidos y consultando el listado completo del maestro, sin
depender de ninguna orden de trabajo.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado en el módulo de Inventario, **When** completa el formulario de
   nuevo producto con datos válidos (material, espesor, dimensiones, stock, punto de pedido) y
   confirma, **Then** el sistema crea el producto en el maestro y le asigna automáticamente un Id
   único y secuencial.
2. **Given** un usuario que intenta confirmar el alta de un producto con algún campo obligatorio
   vacío, **When** envía el formulario, **Then** el sistema rechaza el alta y señala los campos
   faltantes.
3. **Given** un producto ya existente en el maestro con un material, espesor, largo y ancho
   determinados (valores exactos), **When** el usuario intenta crear otro producto con exactamente
   los mismos valores en esos cuatro campos, **Then** el sistema rechaza el alta e informa que ya
   existe un producto con esas características.
4. **Given** un usuario que edita un producto existente modificando un campo permitido (ej. punto
   de pedido) con un valor válido, **When** guarda los cambios, **Then** el sistema persiste el
   nuevo valor y lo refleja en el listado de productos.
5. **Given** un usuario que intenta editar un producto, **When** accede al formulario de edición,
   **Then** el campo de stock comprometido está bloqueado para edición manual.
6. **Given** un usuario autenticado en el módulo de Inventario, **When** accede a la sección de
   productos, **Then** el sistema muestra el listado completo de productos del maestro.
7. **Given** dos productos existentes en el maestro, **When** el usuario edita el material, espesor
   o dimensiones de uno de ellos de forma que coincide exactamente con el otro, **Then** el sistema
   rechaza la edición e informa el conflicto, igual que lo haría con un alta duplicada.

---

### User Story 5 - Configuración del margen de tolerancia dimensional (Priority: P5)

Un empleado autenticado puede consultar y ajustar, desde un apartado de configuración, el margen
de tolerancia dimensional que el sistema usa para decidir si dos productos con pequeñas
diferencias de medida son "el mismo" producto a efectos de compromiso de stock (Oficina) y alta de
recortes (Taller).

**Why this priority**: Ajusta el comportamiento de coincidencia de las historias 2 y 3, pero el
sistema es utilizable con el valor por defecto sin que el usuario lo toque nunca; por eso es la de
menor prioridad relativa.

**Independent Test**: Puede probarse de forma aislada consultando el valor por defecto,
modificándolo, y verificando en un caso de coincidencia de producto (independiente de esta
historia) que el nuevo valor configurado es el que se usa.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado en el apartado de Configuración, **When** visualiza el Margen
   de Tolerancia Dimensional sin haberlo modificado previamente, **Then** el sistema muestra el
   valor por defecto de 1.0 mm.
2. **Given** un usuario que modifica el Margen de Tolerancia Dimensional a un valor válido y lo
   guarda, **When** el sistema realiza una búsqueda de coincidencia de producto (en los flujos de
   Oficina o Taller), **Then** utiliza el nuevo valor configurado en lugar del valor por defecto.

---

### Edge Cases

- ¿Qué pasa si el PDF subido no sigue la estructura de tablas esperada (Datos Generales, Datos de
  Elaboración, Datos de Producción, listado de Piezas) o está dañado/no es el formato del software
  de corte esperado? El sistema debe informar que no pudo extraer datos y permitir al usuario
  cargarlos manualmente en lugar de bloquear la operación.
- ¿Qué pasa si dos o más productos existentes caen dentro del margen de tolerancia de una búsqueda
  de coincidencia (ambigüedad de match)? El sistema resuelve la ambigüedad automáticamente
  eligiendo el producto con la menor diferencia de dimensiones (largo + ancho) respecto al valor
  buscado (ver FR-031), para no comprometer/incrementar el producto equivocado. Si dos o más
  productos quedan exactamente empatados en esa diferencia, el sistema desempata eligiendo el de
  menor Id (el creado primero).
- ¿Qué pasa si el usuario escanea o ingresa un código NEST que no existe en el sistema? El sistema
  debe informar que no se encontró ninguna orden con ese código, sin generar error no manejado.
  ¿Qué pasa si el usuario intenta finalizar dos veces la misma orden (ya "cerrada")? El sistema
  debe impedirlo e informar que la orden ya fue cerrada.
- ¿Qué pasa si el usuario cierra la sesión o esta expira (24 h de inactividad) mientras revisa
  datos extraídos de un PDF sin confirmar? Los datos no confirmados no deben quedar persistidos.
- ¿Qué pasa si se sube un archivo de corte cuya multiplicidad o dimensiones coinciden con una
  orden ya cargada previamente? No hay deduplicación de órdenes por contenido; cada carga
  confirmada genera una orden y un código NEST nuevos.
- ¿Qué pasa si dos usuarios operan simultáneamente sobre el stock del mismo producto (ej. dos
  órdenes de Oficina se confirman a la vez, u Oficina y Taller lo tocan al mismo tiempo)? Cada
  operación aplica su propio incremento/decremento de forma atómica sobre el valor vigente en ese
  momento (ver FR-032); ninguna de las dos pisa el resultado de la otra.
- ¿Qué pasa si el dispositivo de Taller pierde conectividad con el servidor durante el escaneo o
  cierre de una orden? El sistema requiere conexión activa para operar (ver FR-021): muestra un
  error claro indicando la falta de conexión y no permite escanear ni cerrar la orden hasta que la
  conectividad se restablezca; no hay modo offline ni cola de sincronización posterior.

## Requirements *(mandatory)*

### Functional Requirements

**Acceso y seguridad**

- **FR-001**: El sistema MUST presentar una pantalla de inicio de sesión que solicite email y
  contraseña antes de otorgar acceso a cualquier funcionalidad.
- **FR-002**: El sistema MUST redirigir a la pantalla de inicio de sesión a todo usuario no
  autenticado que intente acceder a cualquier página del sistema.
- **FR-003**: El sistema MUST permitir el autorregistro de nuevos usuarios (email y contraseña) de
  forma simple, rechazando el alta si el email ya está registrado. La contraseña MUST tener un
  mínimo de 8 caracteres, sin otro requisito de composición (no se exige mayúscula, número ni
  símbolo).
- **FR-004**: El sistema MUST otorgar a todo usuario autenticado el mismo nivel de acceso a todos
  los módulos (Oficina, Taller, Inventario, Configuración), dado que no existen roles ni permisos
  diferenciados en esta etapa.
- **FR-005**: El sistema MUST almacenar las contraseñas mediante un mecanismo de hash seguro e
  irreversible, nunca en texto plano.
- **FR-006**: El sistema MUST expirar automáticamente la sesión de un usuario tras 24 horas de
  inactividad.
- **FR-006a**: El sistema MUST permitir a un usuario autenticado cerrar sesión de forma explícita
  (logout) en cualquier momento, descartando el token localmente y redirigiéndolo a la pantalla de
  inicio de sesión.

**Captura y validación del archivo de corte (Oficina)**

- **FR-007**: El sistema MUST permitir a un usuario autenticado subir un archivo de corte en
  formato PDF, y MUST rechazar archivos con cualquier otra extensión informando el motivo. El
  sistema MUST rechazar archivos que superen los 20 MB, informando el motivo.
- **FR-008**: El sistema MUST extraer del PDF, como propuesta editable, los datos generales
  (multiplicidad, dimensiones, espesor, material, tiempo de ejecución estimado) y el listado de
  piezas con sus cantidades.
- **FR-009**: El sistema MUST extraer las dimensiones (largo x ancho) de los ítems identificados
  como recorte sobrante ("Saved scrap") a partir del nombre técnico del ítem.
- **FR-010**: El sistema MUST presentar todos los datos extraídos al usuario para su revisión y
  MUST permitir editar cualquier valor antes de confirmar.
- **FR-011**: El sistema MUST impedir que cualquier dato extraído del PDF se persista en la base
  de datos sin confirmación explícita del usuario.
- **FR-012**: El sistema MUST generar, al confirmar, un código NEST único y secuencial con el
  formato `NEST-` seguido del número secuencial con padding a 6 dígitos (ej. `NEST-000001`), y MUST
  guardar la orden de trabajo resultante con estado "vigente".
- **FR-013**: El sistema MUST generar e imprimir, al confirmar la orden, un documento que incluya
  un código de barras del código NEST y el detalle de piezas; ese código de barras MUST ser
  decodificable por un lector estándar a resolución de impresión típica, no solo reconocible como
  imagen en pantalla.
- **FR-014**: El sistema MUST comprometer, al confirmar la orden, el stock del producto cuyo
  material, espesor y dimensiones coincidan (dentro del margen de tolerancia configurado) con lo
  indicado en la orden, en una cantidad igual a la multiplicidad (una unidad de stock por cada
  chapa física consumida).
- **FR-015**: El sistema MUST advertir al usuario si, al confirmar la orden, no existe ningún
  producto coincidente en el maestro, y MUST ofrecer la creación automática del producto con los
  datos técnicos extraídos y stock físico en cero si el usuario lo acepta. Si la creación
  automática del producto falla, el sistema MUST revertir toda la confirmación de la orden (nada
  se persiste) de forma todo-o-nada, permitiendo al usuario reintentar desde la propuesta ya
  revisada.
- **FR-016**: El sistema MUST mostrar un indicador visual de alerta (badge/ícono junto al valor de
  stock, en el listado de productos del módulo de Inventario) cuando el stock disponible (stock
  físico menos stock comprometido) de un producto alcance o caiga por debajo de su punto de
  pedido, sin impedir que el proceso continúe.
- **FR-017**: El sistema MUST permitir listar las órdenes de trabajo filtrando por estado
  (vigente/cerrada) y buscando por código NEST (coincidencia parcial), de forma combinable; sin
  filtros, MUST mostrar todas las órdenes.

**Cierre en taller**

- **FR-018**: El sistema MUST permitir localizar una orden de trabajo escaneando su código de
  barras o ingresando manualmente el código NEST, mostrando en pantalla la orden asociada en
  ambos casos.
- **FR-019**: El sistema MUST permitir a un usuario autenticado finalizar una orden "vigente",
  cambiando su estado a "cerrada".
- **FR-020**: El sistema MUST descontar, al finalizar una orden, el stock físico y el stock
  comprometido del producto correspondiente, en una cantidad igual a la multiplicidad (ver
  FR-014).
- **FR-021**: El sistema MUST requerir conectividad activa con el servidor para operar en
  cualquier módulo (Oficina, Taller, Inventario, Configuración); esto incluye, en particular,
  escanear o ingresar manualmente un código NEST y finalizar una orden en Taller. Si no hay
  conectividad, MUST mostrar un error claro y MUST impedir la operación hasta que la conexión se
  restablezca, sin ofrecer un modo offline ni sincronización diferida.
- **FR-022**: El sistema MUST dar de alta como nuevo producto en el maestro cualquier recorte
  sobrante detallado en la orden que no tenga coincidencia (material, espesor y dimensiones dentro
  del margen de tolerancia) con un producto existente, al finalizar la orden.
- **FR-023**: El sistema MUST incrementar el stock del producto existente que coincida (material,
  espesor y dimensiones dentro del margen de tolerancia) con un recorte sobrante detallado en la
  orden, en la cantidad detallada, al finalizar la orden.

**Gestión del maestro de productos (Inventario)**

- **FR-024**: El sistema MUST permitir a un usuario autenticado crear un nuevo producto
  registrando material, espesor, dimensiones (largo y ancho), stock físico y punto de pedido, y
  MUST rechazar el alta señalando los campos faltantes si falta alguno de esos datos.
- **FR-025**: El sistema MUST asignar automáticamente un identificador único y secuencial a cada
  producto creado.
- **FR-026**: El sistema MUST rechazar el alta manual de un producto si ya existe otro con el
  mismo material, espesor y dimensiones (largo y ancho) exactos; esta validación es independiente
  del margen de tolerancia, que solo aplica a las búsquedas de coincidencia de Oficina y Taller.
- **FR-027**: El sistema MUST permitir editar un producto existente, excepto su campo de stock
  comprometido, que solo se actualiza mediante el cierre de una orden de trabajo. Si la edición
  modifica material, espesor o dimensiones, el sistema MUST aplicar la misma validación de
  unicidad de FR-026 (rechazar si el resultado coincide exactamente con otro producto existente) y
  MUST rechazar la edición señalando el conflicto en ese caso.
- **FR-028**: El sistema MUST permitir a un usuario autenticado visualizar el listado completo de
  productos del maestro.

**Configuración**

- **FR-029**: El sistema MUST proveer un apartado de configuración donde consultar y modificar el
  Margen de Tolerancia Dimensional (en mm), con un valor por defecto de 1.0 mm cuando no fue
  modificado. El sistema MUST rechazar valores no positivos (cero o negativos); no hay límite
  superior explícito.
- **FR-030**: El sistema MUST utilizar el valor de Margen de Tolerancia Dimensional vigente en
  configuración para toda búsqueda de coincidencia de producto por dimensiones (Oficina y Taller).
- **FR-031**: Cuando una búsqueda de coincidencia de producto (Oficina o Taller) encuentre más de
  un producto cuyo material, espesor y dimensiones caigan dentro del margen de tolerancia
  configurado, el sistema MUST elegir de forma determinística el producto con la menor diferencia
  de dimensiones (largo + ancho) respecto al valor buscado, sin requerir intervención manual del
  usuario. Si dos o más productos quedan exactamente empatados en esa diferencia, el sistema MUST
  desempatar eligiendo el producto con menor Id (el creado primero).
- **FR-032**: Toda actualización de stock (compromiso, descuento, alta o incremento por recorte)
  MUST aplicarse como una operación atómica de incremento/decremento sobre el valor vigente del
  producto en el momento de la escritura, de forma que operaciones concurrentes sobre el mismo
  producto no se pisen entre sí ni pierdan actualizaciones.

### Key Entities

- **Usuario**: persona autenticada del sistema. Atributos clave: email (identificador único),
  contraseña (almacenada como hash). No tiene rol ni permisos diferenciados.
- **Orden de trabajo**: representa un archivo de corte procesado. Atributos clave: código NEST
  (único, secuencial), estado (vigente/cerrada), datos generales (multiplicidad — cantidad de
  chapas físicas consumidas por la orden, dimensiones, espesor, material, tiempo de ejecución
  estimado), listado de piezas asociadas, listado de recortes sobrantes asociados. Se relaciona
  con el producto de chapa que compromete/descuenta y con los productos de recorte que da de alta/
  incrementa.
- **Pieza**: ítem individual dentro de una orden de trabajo. Atributos clave: descripción,
  cantidad. Pertenece a una orden de trabajo.
- **Recorte**: recorte sobrante declarado dentro de una orden de trabajo. Atributos clave:
  dimensiones (largo x ancho en mm), que pueden quedar incompletas hasta que el usuario las
  completa. Pertenece a una orden de trabajo; al cerrarse la orden se vincula al producto que se
  da de alta o incrementa en el maestro.
- **Producto**: ítem del maestro de inventario, ya sea chapa base o recorte sobrante. Atributos
  clave: Id único y secuencial, material, espesor (mm), dimensiones (largo x ancho en mm), stock
  físico, stock comprometido, punto de pedido.
- **Configuración del sistema**: parámetros globales de operación. Atributo clave: Margen de
  Tolerancia Dimensional (mm), con valor por defecto 1.0 mm.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Al menos el 98% de los campos individuales (datos generales, piezas y recortes) de
  una muestra de archivos de corte estándar (`Archivos de Corte/`) se extraen correctamente sin que
  el usuario deba corregirlos manualmente, medido campo por campo (no por documento completo).
- **SC-002**: El sistema muestra los datos extraídos de un archivo de corte al usuario para su
  revisión en menos de 10 segundos desde que termina la carga del PDF.
- **SC-003**: Los listados y búsquedas (órdenes de trabajo, productos) devuelven resultados en
  menos de 2 segundos en el 95% de los casos.
- **SC-004**: El código de barras impreso en una orden de trabajo es leído correctamente en el
  primer intento por un lector óptico o una cámara de dispositivo móvil estándar, a resolución de
  impresión típica.
- **SC-005**: Un usuario puede completar el ciclo completo "subir PDF → revisar y confirmar datos →
  obtener orden con código NEST impreso" sin intervención de otra persona ni de un sistema externo.
- **SC-006**: Ningún dato extraído automáticamente de un PDF llega a figurar en el inventario o en
  el listado de órdenes sin haber pasado por una confirmación explícita del usuario.
- **SC-007**: Un usuario sin sesión iniciada no puede visualizar ni modificar ningún dato de
  órdenes de trabajo o del maestro de productos en ningún momento.
- **SC-008**: La duplicación de productos por variaciones mínimas de medida (dentro del margen de
  tolerancia configurado) se mantiene en cero durante la operación normal de Oficina y Taller.

## Assumptions

- El PDF subido siempre proviene del mismo software CAD/CAM (Salvagnini) y mantiene una
  estructura de tablas consistente entre archivos (Datos Generales, Datos de Elaboración, Datos de
  Producción, listado de Piezas); variaciones mayores de formato están fuera del alcance de esta
  versión y se resuelven pidiendo carga manual.
- Todos los usuarios autenticados comparten el mismo espacio de datos (workspace compartido); no
  hay aislamiento de datos por usuario, cuenta o sucursal.
- No hay proceso de aprobación de compras: la alerta de punto de pedido es solo informativa y no
  bloquea ni deriva en una orden de compra.
- El volumen de operación es el de una única empresa (no multi-tenant) con una cantidad moderada de
  usuarios concurrentes (equipo de oficina y taller), no un servicio masivo multi-cliente.
- "Órdenes de compra", "facturación" y "generación de remitos" quedan fuera de alcance de esta
  especificación, tal como en el PRD de origen.
- La configuración de roles y permisos diferenciados queda fuera de alcance; todo usuario
  autenticado tiene acceso total a todos los módulos.
- No hay bloqueo de cuenta ni rate limiting ante intentos fallidos repetidos de login; cada
  intento fallido responde simplemente 401 (ver Clarifications, Session 2026-07-22).
- El requisito de conectividad activa (sin modo offline) aplica por igual a los cuatro módulos
  (Oficina, Taller, Inventario, Configuración); FR-021 lo hace explícito solo para Taller por su
  contexto de hardware distinto, no porque los demás módulos toleren operar sin conexión.
- La eliminación de productos u órdenes de trabajo no está soportada en esta versión; los datos,
  una vez creados, solo se editan (productos) o cambian de estado (órdenes), nunca se borran.
- No hay auditoría ni trazabilidad de autoría (no se registra qué usuario confirmó una orden o
  editó un producto), consistente con el workspace compartido sin roles ni permisos diferenciados
  (FR-004).
