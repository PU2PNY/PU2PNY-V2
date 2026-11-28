/* PU2PNY-V2 UI translation layer (PT/EN/ES).
   Pages are authored in pt-BR; this layer rewrites visible text, placeholders,
   titles and aria-labels into EN or ES from the catalog D, keyed by the exact
   Portuguese source string with value [English, Spanish]. A view is never shown
   with two languages mixed: an unknown string with Portuguese letters falls back
   to a neutral system message rather than a half translation. Mirrors the engine
   and conventions of the shipping ui-language.js. */
(()=>{
let language=(localStorage.getItem('pu2pny-language')||'pt').toLowerCase();
if(!/^(pt|en|es)$/.test(language))language='pt';

const D={
'Ao Vivo':['Live','En vivo'],'Internet':['Internet','Internet'],'Protocolos':['Protocols','Protocolos'],
'Direct':['Direct','Direct'],'APRS':['APRS','APRS'],'Histórico':['History','Historial'],
'Display':['Display','Pantalla'],'Sistema':['System','Sistema'],'Expert':['Expert','Experto'],'Básico':['Basic','Básico'],
'Hotspot de Rádio Amador':['Amateur Radio Hotspot','Hotspot de Radioaficionado'],
'☀ Claro':['☀ Light','☀ Claro'],'☾ Escuro':['☾ Dark','☾ Oscuro'],
'Rádio':['Radio','Radio'],'Rádio ativo':['Radio active','Radio activo'],'Rádio parado':['Radio stopped','Radio detenido'],
'Internet OK':['Internet OK','Internet OK'],'Internet offline':['Internet offline','Internet sin conexión'],'Internet atenção':['Internet warning','Internet atención'],
'Hotspot em tempo real · RF, gateway e Internet.':['Hotspot in real time · RF, gateway and Internet.','Hotspot en tiempo real · RF, gateway e Internet.'],
'Conectado ao servidor':['Connected to the server','Conectado al servidor'],
'Desconectado do servidor':['Disconnected from the server','Desconectado del servidor'],
'Gateway ativo, aguardando link do servidor.':['Gateway active, waiting for the server link.','Gateway activo, esperando el enlace del servidor.'],
'Perfil selecionado não está ativo.':['Selected profile is not active.','El perfil seleccionado no está activo.'],
'Ativar perfil selecionado':['Activate selected profile','Activar perfil seleccionado'],
'AGUARDANDO':['WAITING','ESPERANDO'],'TX ATIVO':['TX ACTIVE','TX ACTIVO'],'RX ATIVO':['RX ACTIVE','RX ACTIVO'],
'Sem transmissão':['No transmission','Sin transmisión'],'Monitorando RF e Internet':['Monitoring RF and Internet','Monitoreando RF e Internet'],
'Sinal recebido pelo rádio':['Signal received by radio','Señal recibida por radio'],'Recebendo pela Internet':['Receiving over the Internet','Recibiendo por Internet'],
'Tempo':['Time','Tiempo'],'TOT restante':['TOT remaining','TOT restante'],
'Protocolo':['Protocol','Protocolo'],'Destino':['Destination','Destino'],'Slot':['Slot','Slot'],'Color Code':['Color Code','Color Code'],
'Conexão':['Connection','Conexión'],'Gateway ativo':['Gateway active','Gateway activo'],'Aguardando':['Waiting','Esperando'],
'Servidor / destino':['Server / destination','Servidor / destino'],'Servidor / refletor':['Server / reflector','Servidor / reflector'],
'Servidor / sala/refletor':['Server / room/reflector','Servidor / sala/reflector'],
'Frequência':['Frequency','Frecuencia'],'CPU / Temp.':['CPU / Temp.','CPU / Temp.'],
'Direção':['Direction','Dirección'],'Transmissão (TX)':['Transmit (TX)','Transmisión (TX)'],'Recepção (RX)':['Receive (RX)','Recepción (RX)'],
'Sem atividade':['No activity','Sin actividad'],'Latência':['Latency','Latencia'],'Perda':['Loss','Pérdida'],'Jitter':['Jitter','Jitter'],
'Atividade recente':['Recent activity','Actividad reciente'],'Aguardando transmissões':['Waiting for transmissions','Esperando transmisiones'],
'Todos':['All','Todos'],'Indicativo':['Callsign','Indicativo'],'Nome':['Name','Nombre'],'Estação':['Station','Estación'],
'Cidade':['City','Ciudad'],'País':['Country','País'],'Status':['Status','Estado'],'Módulo / TG':['Module / TG','Módulo / TG'],'Horário':['Time','Hora'],
'Aguardando atividade...':['Waiting for activity...','Esperando actividad...'],'Nenhuma atividade registrada para este filtro.':['No activity recorded for this filter.','Ninguna actividad registrada para este filtro.'],
'Atualizar agora':['Refresh now','Actualizar ahora'],
'Saúde da comunicação':['Communication health','Salud de la comunicación'],
'Sinal RF':['RF signal','Señal RF'],'Wi-Fi / Uplink':['Wi-Fi / Uplink','Wi-Fi / Enlace'],'Link ativo':['Link active','Enlace activo'],
'Aguardando RX do rádio':['Waiting for radio RX','Esperando RX de radio'],
'Hotspot / Protocolos':['Hotspot / Protocols','Hotspot / Protocolos'],
'Troca de protocolo':['Protocol switch','Cambio de protocolo'],
'Escolha o protocolo ativo. A troca é transacional: salva o perfil, aplica e confirma, com retorno automático se falhar.':['Choose the active protocol. The switch is transactional: it saves the profile, applies and confirms, with automatic rollback on failure.','Elija el protocolo activo. El cambio es transaccional: guarda el perfil, aplica y confirma, con reversión automática si falla.'],
'Perfil do protocolo':['Protocol profile','Perfil del protocolo'],'configurar':['configure','configurar'],
'Servidor / rede':['Server / network','Servidor / red'],'Código de cor':['Color Code','Código de color'],'Slot de tempo':['Time Slot','Slot de tiempo'],
'Salvar perfil':['Save profile','Guardar perfil'],'Ativar perfil':['Activate profile','Activar perfil'],
'Visibilidade do hotspot':['Hotspot visibility','Visibilidad del hotspot'],
'Público':['Public','Público'],'Privado':['Private','Privado'],
'Público aparece nos diretórios e mapas da rede. Privado opera sem publicar o indicativo nas listas públicas.':['Public appears in the network directories and maps. Private operates without publishing the callsign in public lists.','Público aparece en los directorios y mapas de la red. Privado opera sin publicar el indicativo en las listas públicas.'],
'Internet e rede':['Internet and network','Internet y red'],
'Wi‑Fi, conexão via cabo, qualidade e redes de backup.':['Wi-Fi, wired connection, quality and backup networks.','Wi-Fi, conexión por cable, calidad y redes de respaldo.'],
'Conexão ativa':['Active connection','Conexión activa'],'Interface':['Interface','Interfaz'],'SSID':['SSID','SSID'],
'Sinal':['Signal','Señal'],'Qualidade da Internet':['Internet quality','Calidad de Internet'],'IP':['IP','IP'],
'Conexão via cabo':['Wired connection','Conexión por cable'],'Link ativo':['Link active','Enlace activo'],'Sem link':['No link','Sin enlace'],
'Velocidade':['Speed','Velocidad'],
'Rede Wi‑Fi 1':['Wi-Fi Network 1','Red Wi-Fi 1'],'Rede Wi‑Fi 2':['Wi-Fi Network 2','Red Wi-Fi 2'],
'Rede principal e rede de backup':['Primary and backup network','Red principal y de respaldo'],
'Buscar redes':['Scan networks','Buscar redes'],'↻ Buscar redes':['↻ Scan networks','↻ Buscar redes'],
'Trocar rede atual':['Change current network','Cambiar red actual'],'Adicionar rede de backup':['Add backup network','Agregar red de respaldo'],
'Rede encontrada':['Network found','Red encontrada'],'Ou adicionar manualmente':['Or add manually','O agregar manualmente'],
'Nome da rede (SSID)':['Network name (SSID)','Nombre de red (SSID)'],'Senha':['Password','Contraseña'],'Mostrar':['Show','Mostrar'],'Ocultar':['Hide','Ocultar'],
'Aplicar rede principal':['Apply primary network','Aplicar red principal'],'Salvar rede de backup':['Save backup network','Guardar red de respaldo'],
'A segunda rede funciona como backup. Se a atual cair, o PU2PNY tenta a outra; a escolha automática considera o sinal sem trocar por diferenças pequenas. Ethernet tem prioridade quando disponível.':['The second network works as a backup. If the current one drops, PU2PNY tries the other; automatic selection considers the signal without switching for small differences. Ethernet takes priority when available.','La segunda red funciona como respaldo. Si la actual cae, PU2PNY intenta la otra; la selección automática considera la señal sin cambiar por diferencias pequeñas. Ethernet tiene prioridad cuando está disponible.'],
'Configuração do display':['Display configuration','Configuración de pantalla'],'Display / Nextion':['Display / Nextion','Pantalla / Nextion'],
'Detecção automática, brilho, rotação e informações do MMDVM em todas as telas.':['Automatic detection, brightness, rotation and MMDVM information on every screen.','Detección automática, brillo, rotación e información del MMDVM en todas las pantallas.'],
'Estado atual':['Current state','Estado actual'],'Tipo':['Type','Tipo'],'Modelo':['Model','Modelo'],'Resolução':['Resolution','Resolución'],
'Integração':['Integration','Integración'],'Driver':['Driver','Controlador'],'Porta MMDVM':['MMDVM port','Puerto MMDVM'],
'Detectar display':['Detect display','Detectar pantalla'],'Redetectar hardware':['Redetect hardware','Redetectar hardware'],
'Tipo de tela':['Screen type','Tipo de pantalla'],'OLED':['OLED','OLED'],'LED':['LED','LED'],'Nextion':['Nextion','Nextion'],
'Usar Nextion pela MMDVM':['Use Nextion through MMDVM','Usar Nextion mediante MMDVM'],
'Modelo / tamanho':['Model / size','Modelo / tamaño'],'Auto detectar':['Auto detect','Auto detectar'],
'Rotação da tela':['Screen rotation','Rotación de pantalla'],
'Brilho':['Brightness','Brillo'],'Mostrar informações do MMDVM em todas as telas':['Show MMDVM information on every screen','Mostrar información del MMDVM en todas las pantallas'],
'Aplicar Display':['Apply Display','Aplicar pantalla'],
'A MMDVMHost continua dona da porta serial. O sistema impede dois renderizadores simultâneos e só confirma a tela física após retorno COMOK.':['MMDVMHost remains the owner of the serial port. The system prevents two renderers at once and confirms the physical screen only after a COMOK return.','MMDVMHost sigue siendo dueño del puerto serie. El sistema impide dos renderizadores a la vez y solo confirma la pantalla física tras un retorno COMOK.'],
'Relógio, operação do rádio, atualizações e energia.':['Clock, radio operation, updates and power.','Reloj, operación del radio, actualizaciones y energía.'],
'Relógio':['Clock','Reloj'],'Hora local':['Local time','Hora local'],'Fuso horário':['Time zone','Zona horaria'],
'Sincronizado NTP':['NTP synchronized','NTP sincronizado'],'Detectar região e sincronizar':['Detect region and synchronize','Detectar región y sincronizar'],
'Fuso horário manual':['Manual time zone','Zona horaria manual'],'Aplicar fuso manual':['Apply manual time zone','Aplicar zona horaria manual'],
'Operacional':['Operational','Operativo'],'Ligado':['On','Encendido'],'Desligado':['Off','Apagado'],
'Desligar operacional':['Turn off operational','Apagar operativo'],'Ligar operacional':['Turn on operational','Encender operativo'],
'Desligar o operacional para MMDVMHost e gateways, mas mantém painel, rede e acesso para manutenção.':['Turning off operational stops MMDVMHost and gateways but keeps the panel, network and access for maintenance.','Apagar el operativo detiene MMDVMHost y los gateways pero mantiene el panel, la red y el acceso para mantenimiento.'],
'Temperatura':['Temperature','Temperatura'],'RAM':['RAM','RAM'],
'Atualizações':['Updates','Actualizaciones'],'Verificando...':['Checking...','Verificando...'],'Atualizado':['Up to date','Actualizado'],
'Atualização disponível':['Update available','Actualización disponible'],'Verificar atualizações':['Check for updates','Buscar actualizaciones'],
'Baixar atualização':['Download update','Descargar actualización'],'Instalar agora':['Install now','Instalar ahora'],'Ver detalhes':['View details','Ver detalles'],
'Guardar versão atual para rollback':['Keep current version for rollback','Guardar versión actual para rollback'],
'O download ocorre em segundo plano e nada é instalado antes de 100% e da validação SHA‑256.':['The download runs in the background and nothing is installed before 100% and SHA-256 validation.','La descarga ocurre en segundo plano y nada se instala antes del 100% y la validación SHA-256.'],
'Energia':['Power','Energía'],'Reiniciar hotspot':['Restart hotspot','Reiniciar hotspot'],'Desligar completamente':['Power off','Apagar completamente'],
'Use os botões antes de cortar a alimentação. Reiniciar e desligar exigem confirmação.':['Use the buttons before cutting power. Restart and power off require confirmation.','Use los botones antes de cortar la alimentación. Reiniciar y apagar requieren confirmación.'],
'Carregando...':['Loading...','Cargando...'],'Indisponível':['Unavailable','No disponible'],'Versão':['Version','Versión'],
'Cockpit técnico em tempo real. Ajustes RF usam confirmação e rollback.':['Technical cockpit in real time. RF changes use confirmation and rollback.','Cabina técnica en tiempo real. Los ajustes RF usan confirmación y reversión.'],
'Memória':['Memory','Memoria'],'Saúde dos serviços':['Service health','Salud de los servicios'],'Hardware':['Hardware','Hardware'],
'Porta / baud':['Port / baud','Puerto / baud'],'Uplink':['Uplink','Enlace'],'Resumo operacional':['Operational summary','Resumen operativo'],
'Rede / rota':['Network / route','Red / ruta'],'Ativo':['Active','Activo'],'Parado':['Stopped','Detenido'],
'PU2PNY Direct':['PU2PNY Direct','PU2PNY Direct'],
'QSO ponto a ponto com fallback criptografado quando NAT/CGNAT impedir o caminho direto.':['Point-to-point QSO with encrypted fallback when NAT/CGNAT blocks the direct path.','QSO punto a punto con respaldo cifrado cuando NAT/CGNAT impide la ruta directa.'],
'Contatos pareados':['Paired contacts','Contactos emparejados'],'Nenhum contato.':['No contacts.','Sin contactos.'],
'Chamar':['Call','Llamar'],'Encerrar':['Hang up','Finalizar'],'Parear':['Pair','Emparejar'],
'APRS / D-PRS':['APRS / D-PRS','APRS / D-PRS'],
'Mensagens APRS. Esta instalação não publica posição, GPS nem beacon; o APRS é usado somente para mensagens.':['APRS messages. This installation does not publish position, GPS or beacons; APRS is used only for messages.','Mensajes APRS. Esta instalación no publica posición, GPS ni balizas; APRS se usa solo para mensajes.'],
'Enviar mensagem':['Send message','Enviar mensaje'],'Indicativo destino':['Destination callsign','Indicativo destino'],
'Mensagem':['Message','Mensaje'],'Enviar':['Send','Enviar'],'Mensagens':['Messages','Mensajes'],'Sem mensagens.':['No messages.','Sin mensajes.'],
'Resumo de atividade':['Activity summary','Resumen de actividad'],'Eventos':['Events','Eventos'],
'RF → Internet':['RF → Internet','RF → Internet'],'Internet → RF':['Internet → RF','Internet → RF'],
'Protocolo mais usado':['Most used protocol','Protocolo más usado'],'Atividade 24h':['24h activity','Actividad 24h'],
'Salvo.':['Saved.','Guardado.'],'Aplicado.':['Applied.','Aplicado.'],'Concluído.':['Completed.','Completado.'],
'Aplicando alteração':['Applying change','Aplicando cambio'],'Enviando, validando e aguardando confirmação do sistema...':['Sending, validating and waiting for system confirmation...','Enviando, validando y esperando la confirmación del sistema...'],
'Alteração aplicada.':['Change applied.','Cambio aplicado.'],'Fechar':['Close','Cerrar']
};

/* Additional static strings used across the panel pages, so every visible
   label, heading, button and notice translates cleanly. Uncatalogued runtime
   status strings use the strict no-mixed-language fallback above. */
Object.assign(D,{
'O sistema verifica o repositório oficial sem instalar silenciosamente.':['The system checks the official repository without installing silently.','El sistema verifica el repositorio oficial sin instalar en silencio.'],
'Instalação segura:':['Safe install:','Instalación segura:'],
'o download ocorre em segundo plano e nada é instalado antes de 100% e da validação SHA‑256. Use alimentação estável; em falha após o início, o sistema tenta restaurar o ponto de retorno automaticamente.':['the download runs in the background and nothing is installed before 100% and SHA-256 validation. Use stable power; on failure after it starts, the system tries to restore the rollback point automatically.','la descarga ocurre en segundo plano y nada se instala antes del 100% y la validación SHA-256. Use alimentación estable; ante una falla tras el inicio, el sistema intenta restaurar el punto de retorno automáticamente.'],
'Não foi possível carregar os fusos horários.':['Could not load the time zones.','No fue posible cargar las zonas horarias.'],
'Estado do atualizador':['Updater state','Estado del actualizador'],'Download':['Download','Descarga'],'Ponto de retorno':['Rollback point','Punto de retorno'],
'Estado':['State','Estado'],'Estado da Internet':['Internet status','Estado de Internet'],'Interface usada':['Interface in use','Interfaz usada'],
'Gateway':['Gateway','Gateway'],'DNS ativo':['Active DNS','DNS activo'],'Destino testado':['Tested target','Destino probado'],'Última atualização':['Last update','Última actualización'],
'“Online” significa que o hotspot tem rota e conectividade observada. Um hop sem resposta ICMP, sozinho, não indica falha.':['“Online” means the hotspot has a route and observed connectivity. A hop with no ICMP reply, by itself, does not indicate failure.','“En línea” significa que el hotspot tiene ruta y conectividad observada. Un salto sin respuesta ICMP, por sí solo, no indica falla.'],
'Protocolo ativo':['Active protocol','Protocolo activo'],'Perfil não configurado':['Profile not configured','Perfil no configurado'],'Configurar':['Configure','Configurar'],'Pronto':['Ready','Listo'],
'A configuração detalhada de servidor, senha e opções do master é feita durante o assistente e reaplicada aqui a cada troca.':['Detailed server, password and master options are set in the wizard and reapplied here on every switch.','La configuración detallada de servidor, contraseña y opciones del master se hace en el asistente y se reaplica aquí en cada cambio.'],
'Prévia':['Preview','Vista previa'],'Detectando':['Detecting','Detectando'],'Identificado':['Identified','Identificado'],'Erro':['Error','Error'],
'Renderer':['Renderer','Renderizador'],'Compatível MMDVMHost nativo':['Native MMDVMHost compatible','Compatible MMDVMHost nativo'],'Layout compatível':['Compatible layout','Diseño compatible'],
'A prévia é conceitual. O conteúdo físico usa somente dados reais do snapshot Ao Vivo.':['The preview is conceptual. The physical content uses only real data from the Live snapshot.','La vista previa es conceptual. El contenido físico usa solo datos reales del snapshot En vivo.'],
'Ver detecção e runtime':['View detection and runtime','Ver detección y runtime'],'Detalhes técnicos':['Technical details','Detalles técnicos'],'Ver JSON do estado':['View state JSON','Ver JSON del estado'],
'Caminho':['Path','Ruta'],'Criptografia':['Encryption','Cifrado'],'Em repouso':['Idle','En reposo'],'Chamando':['Calling','Llamando'],'Chamada recebida':['Incoming call','Llamada entrante'],'Relay criptografado':['Encrypted relay','Relay cifrado'],'Conexão direta':['Direct connection','Conexión directa'],
'Adicionar indicativo/ID':['Add callsign/ID','Agregar indicativo/ID'],'Sessão ponta a ponta; o relay transporta somente pacotes já criptografados. Depois do QSO, o gateway anterior é restaurado automaticamente.':['End-to-end session; the relay carries only already-encrypted packets. After the QSO, the previous gateway is restored automatically.','Sesión de extremo a extremo; el relay transporta solo paquetes ya cifrados. Después del QSO, el gateway anterior se restaura automáticamente.'],
'Saúde dos serviços':['Service health','Salud de los servicios'],'Porta / baud':['Port / baud','Puerto / baud'],'Resumo operacional':['Operational summary','Resumen operativo'],'Rede / rota':['Network / route','Red / ruta'],'Abrir diagnóstico de Internet':['Open Internet diagnostics','Abrir diagnóstico de Internet'],'Raspberry Pi':['Raspberry Pi','Raspberry Pi'],'Wi-Fi':['Wi-Fi','Wi-Fi'],
'Resumo de atividade do hotspot.':['Hotspot activity summary.','Resumen de actividad del hotspot.'],'Eventos 24h':['24h events','Eventos 24h'],'Destinos mais usados':['Most used destinations','Destinos más usados'],'Indicativos mais ativos':['Most active callsigns','Indicativos más activos'],'Aguardando dados...':['Waiting for data...','Esperando datos...'],'Sem registros.':['No records.','Sin registros.'],'Histórico indisponível.':['History unavailable.','Historial no disponible.'],
'Login APRS-IS':['APRS-IS login','Inicio de sesión APRS-IS'],'Último RX':['Last RX','Último RX'],'Última mensagem TX':['Last message TX','Último mensaje TX'],
'Troca de protocolo, perfis e visibilidade do hotspot.':['Protocol switch, profiles and hotspot visibility.','Cambio de protocolo, perfiles y visibilidad del hotspot.'],
'Rotação':['Rotation','Rotación'],'Tipo de tela':['Screen type','Tipo de pantalla'],'Idioma':['Language','Idioma'],
'Verificando...':['Checking...','Verificando...'],'Indisponível':['Unavailable','No disponible']
});
/* Strings added by the owner-review revision (saved networks, identity edit,
   Direct P2P/groups, Nextion front/back, power-off wording, full report). */
Object.assign(D,{
'Redes Wi‑Fi salvas':['Saved Wi-Fi networks','Redes Wi-Fi guardadas'],'Substituir rede principal':['Replace primary network','Reemplazar red principal'],'Substituir rede de backup':['Replace backup network','Reemplazar red de respaldo'],
'Conectada':['Connected','Conectada'],'Principal':['Primary','Principal'],'Backup salvo':['Backup saved','Respaldo guardado'],'Substituir':['Replace','Reemplazar'],'Tornar principal':['Make primary','Hacer principal'],'Rede principal não identificada':['Primary network not identified','Red principal no identificada'],
'Identidade do hotspot':['Hotspot identity','Identidad del hotspot'],'DMR ID':['DMR ID','DMR ID'],'Salvar identidade':['Save identity','Guardar identidad'],
'Indicativo e DMR ID usados pelo rádio, gateways e diretórios. Alterar reaplica o registro nos gateways.':['Callsign and DMR ID used by the radio, gateways and directories. Changing them reapplies the gateway registration.','Indicativo y DMR ID usados por el radio, los gateways y los directorios. Cambiarlos reaplica el registro en los gateways.'],
'Troca de protocolo, perfis e visibilidade do hotspot.':['Protocol switch, profiles and hotspot visibility.','Cambio de protocolo, perfiles y visibilidad del hotspot.'],
'Em preparação':['In preparation','En preparación'],
'Fala direta entre hotspots, sem passar pelo servidor. Crie grupos privados com código secreto e chame contatos ponto a ponto.':['Direct hotspot-to-hotspot talk, without going through the server. Create private groups with a secret code and call contacts point to point.','Comunicación directa entre hotspots, sin pasar por el servidor. Cree grupos privados con código secreto y llame a contactos punto a punto.'],
'A fala direta ponto a ponto e os grupos privados dependem do motor P2P/relay no sistema do hotspot, que ainda não está disponível nesta versão. Esta tela já prepara a configuração; os botões respondem com aviso enquanto o recurso não é ativado.':['Direct point-to-point talk and private groups depend on the P2P/relay engine in the hotspot system, which is not available yet in this version. This screen already prepares the configuration; the buttons respond with a notice until the feature is enabled.','La comunicación directa punto a punto y los grupos privados dependen del motor P2P/relay del sistema del hotspot, que todavía no está disponible en esta versión. Esta pantalla ya prepara la configuración; los botones responden con un aviso hasta que se active la función.'],
'Conexão direta ponto a ponto':['Direct point-to-point connection','Conexión directa punto a punto'],'Meu endereço direto':['My direct address','Mi dirección directa'],
'O áudio vai direto de hotspot para hotspot por UDP. Quando NAT/CGNAT bloqueia o caminho direto, o PU2PNY usa um relay autenticado mantendo a criptografia ponta a ponta. Depois do QSO, o gateway anterior é restaurado automaticamente.':['Audio goes straight from hotspot to hotspot over UDP. When NAT/CGNAT blocks the direct path, PU2PNY uses an authenticated relay while keeping end-to-end encryption. After the QSO, the previous gateway is restored automatically.','El audio va directo de hotspot a hotspot por UDP. Cuando NAT/CGNAT bloquea la ruta directa, PU2PNY usa un relay autenticado manteniendo el cifrado de extremo a extremo. Después del QSO, el gateway anterior se restaura automáticamente.'],
'Chamar um hotspot direto':['Call a direct hotspot','Llamar a un hotspot directo'],'Indicativo / ID do hotspot':['Hotspot callsign / ID','Indicativo / ID del hotspot'],
'Grupos privados':['Private groups','Grupos privados'],'Um grupo privado conecta vários hotspots com um nome e um código secreto. Só quem tem o código entra. Nenhum servidor público participa.':['A private group connects several hotspots with a name and a secret code. Only those with the code can join. No public server takes part.','Un grupo privado conecta varios hotspots con un nombre y un código secreto. Solo quien tiene el código entra. Ningún servidor público participa.'],
'Nome do grupo':['Group name','Nombre del grupo'],'Código secreto':['Secret code','Código secreto'],'Participantes (indicativos/IDs)':['Members (callsigns/IDs)','Participantes (indicativos/IDs)'],'Criar grupo privado':['Create private group','Crear grupo privado'],
'Meus grupos e contatos':['My groups and contacts','Mis grupos y contactos'],'Nenhum grupo ou contato.':['No groups or contacts.','Sin grupos ni contactos.'],'Chamar grupo':['Call group','Llamar al grupo'],'Excluir':['Delete','Eliminar'],'Sem participantes':['No members','Sin participantes'],'Contatos diretos':['Direct contacts','Contactos directos'],'Em repouso':['Idle','En reposo'],'Conectado':['Connected','Conectado'],
'Layout da tela (frente / verso)':['Screen layout (front / back)','Diseño de pantalla (frente / reverso)'],'Frente':['Front','Frente'],'Verso':['Back','Reverso'],'Frente e verso':['Front and back','Frente y reverso'],
'Operação do rádio, atualizações e energia.':['Radio operation, updates and power.','Operación del radio, actualizaciones y energía.'],
'Reiniciar e desligar exigem confirmação. Aguarde o LED apagar antes de cortar a alimentação.':['Restart and power off require confirmation. Wait for the LED to go out before cutting power.','Reiniciar y apagar requieren confirmación. Espere a que el LED se apague antes de cortar la alimentación.'],
'Desligamento completo:':['Full shutdown:','Apagado completo:'],
'o botão abaixo encerra totalmente o hotspot (halt/poweroff). O aparelho fica desligado de verdade e só volta a ligar quando você religar a energia na mão — não há como ligar de novo pelo painel depois de desligado.':['the button below fully shuts the hotspot down (halt/poweroff). The device is truly off and only turns back on when you re-power it by hand — there is no way to turn it on from the panel once it is off.','el botón de abajo apaga por completo el hotspot (halt/poweroff). El equipo queda realmente apagado y solo vuelve a encender cuando usted reconecta la energía a mano — no hay forma de encenderlo desde el panel una vez apagado.'],
'Desligar completamente o hotspot':['Power off the hotspot completely','Apagar completamente el hotspot'],
'Relatório completo do sistema':['Full system report','Informe completo del sistema'],
'Gera um único relatório com todas as verificações do sistema — hardware, RF/MMDVM, protocolos, rede, serviços, display, atualização e logs — em um arquivo para baixar e anexar em diagnósticos.':['Generates a single report with every system check — hardware, RF/MMDVM, protocols, network, services, display, update and logs — as one file to download and attach to diagnostics.','Genera un único informe con todas las verificaciones del sistema — hardware, RF/MMDVM, protocolos, red, servicios, pantalla, actualización y registros — en un archivo para descargar y adjuntar a diagnósticos.'],
'Gerar relatório completo':['Generate full report','Generar informe completo'],'Baixar relatório':['Download report','Descargar informe']
});
const loose={en:[[/\bMHz\b/g,'MHz']],es:[[/\bMHz\b/g,'MHz']]};
function normalizeIncoming(t){return String(t==null?'':t).replace(/\s+/g,' ').trim()}
const ptLeak=/[ãõç]|(?:não|aplicar|salvar|fuso|horário|relógio|rede|servidor|indicativo|cidade|país|estado|erro|falha|aguardando|conectando|desconectado|atualizar|configuração|senha|mensagem|voltar|continuar|reiniciar|desligar|ligado|idioma|histórico|protocolo|frequência|sinal|chamada|rádio|anterior|manual|automática|região|rotação|brilho)/i;
function strictUnknown(original){
  const technical=(String(original).match(/(?:HTTP\s*)?\b\d{3}\b|\b\d+(?:[.,]\d+)?\s*(?:ms|s|MHz|Hz|dBm|%|MB|GB)\b|\b[A-Z0-9_-]{3,}\b/g)||[]).slice(0,4).join(' · ');
  const base=language==='en'?'System message.':language==='es'?'Mensaje del sistema.':'Mensagem do sistema.';
  return technical?base+' '+technical:base;
}
function tx(text){
  const trimmed=normalizeIncoming(text);if(!trimmed)return trimmed;
  if(language==='pt')return trimmed;
  if(D[trimmed])return D[trimmed][language==='en'?0:1];
  let out=trimmed;for(const pair of loose[language]||[])out=out.replace(pair[0],pair[1]);
  if(ptLeak.test(out))return strictUnknown(trimmed);
  return out;
}
const originals=new WeakMap();
function translateNode(node){
  if(!node||!node.parentElement||['SCRIPT','STYLE','CODE','PRE'].includes(node.parentElement.tagName))return;
  const text=node.textContent.trim();if(!text)return;
  let base=originals.get(node);if(!base){base=text;originals.set(node,base)}
  const wanted=language==='pt'?base:tx(base);
  if(text!==wanted)node.textContent=node.textContent.replace(text,wanted);
}
function translate(){
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;while(node=walker.nextNode())translateNode(node);
  document.querySelectorAll('input[placeholder],textarea[placeholder]').forEach(el=>{const p=el.dataset.pnyOriginalPlaceholder||el.placeholder;if(!el.dataset.pnyOriginalPlaceholder)el.dataset.pnyOriginalPlaceholder=p;el.placeholder=language==='pt'?p:tx(p)});
  document.querySelectorAll('[title],[aria-label]').forEach(el=>{for(const a of ['title','aria-label']){if(!el.hasAttribute(a))continue;const key='pnyOriginal'+a.replace('-','');const p=el.dataset[key]||el.getAttribute(a);if(!el.dataset[key])el.dataset[key]=p;el.setAttribute(a,language==='pt'?p:tx(p))}});
  document.documentElement.lang=language==='pt'?'pt-BR':language;
}
function persistLanguage(v){try{fetch('/api/language',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language:v}),cache:'no-store'}).catch(()=>{})}catch(_){}}
function setLanguage(v,persist){v=String(v||'').toLowerCase();if(!/^(pt|en|es)$/.test(v))return;language=v;localStorage.setItem('pu2pny-language',language);const s=document.getElementById('language');if(s)s.value=language;if(persist!==false)persistLanguage(language);translate()}
function bind(){const s=document.getElementById('language');if(s){s.value=language;s.onchange=()=>setLanguage(s.value,true)}}
bind();translate();document.documentElement.classList.remove('pny-i18n-pending');
try{fetch('/api/language',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(v=>{if(v&&/^(pt|en|es)$/.test(v.language||''))setLanguage(v.language,false)}).catch(()=>{})}catch(_){}
let translating=false;new MutationObserver(()=>{if(translating)return;translating=true;queueMicrotask(()=>{try{bind();translate()}finally{translating=false}})}).observe(document.body,{subtree:true,childList:true,characterData:true});
window.translateNavigation=translate;window.PNYT=tx;window.PNYSetLanguage=setLanguage;window.PNYLocale=()=>language==='en'?'en-US':language==='es'?'es-ES':'pt-BR';
})();
