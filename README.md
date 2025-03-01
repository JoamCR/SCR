SCR: Sistema de Control de Reportes
Es un sistema diseñado a la medida para un taller de cómputo cuyo flujo de trabajo es el siguiente:
   un usuario cualquiera puede recepcionar un equipo, solo ingresa detalles del cliente y detalles del equipo, incluso tiene un checkbox para seleccionar si se deja algun accesorio extra
   un técnico (con su usuario) ingresar y puede ver la lista de servicios en la pagina principal
   el técnico selecciona el servicio y le da retroalimentación, su diagnóstico, la sugerencia y la solución, incluyendo fotos de antes, durante y después del servicio 
   cuando el técnico concluye y selecciona "servicio finalizado" se habilita una vista previa de una hoja de servicio o reporte
   se configura el membrete de la Orden de Servicio y se validan los datos, posteriormente validado, se descarga el PDF para firmar y entregar al cliente

El gerente es el unico que puede crear y deshabilitar usuarios para el sistema, y puede ver tpdo el viclo de vida de los servicios
No se integra (por el momento) algún modulo para conectar directamente con el cliente, pues es a medida y el gerente contacta directamente a los clientes

El sistema está desarrollado en Phyton, con flask en su nucleo, complementado con, HTML, JS y CSS y dividido en diferentes módulos
*aún en desarrollo 
