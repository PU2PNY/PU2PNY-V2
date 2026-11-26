# PU2PNY-V2 — integração completa e limite de 80 MB

**Situação em 26/11/2026:** EM DESENVOLVIMENTO; imagem V2 completa de até 80.000.000 bytes **NÃO ENTREGUE**.

## Baselines e evidência verificadas
- Repositório: `PU2PNY/PU2PNY-V2`.
- Branch TEST-2: `build/v2-test-2`, commit `34e6bab0e1b99e95c1a4b79c11198d8d89f9b90e`.
- Última publicação V2: `pu2pny-v2-test-2`. Arquivo ARM32 `pu2pny-32-v2-test-2.img.xz` tem **729.802.744 bytes**, embora validado no CI; não atingiu 80 MB. TEST-2 aprovado em hardware pelo mantenedor em 26/11/2026. O relato aprova a imagem como baseline, sem detalhar resultados por função; a própria release conserva a classificação original.
- Branch mínima: `build/v2-minimal-80mb`, commit `ec944beca0b81c63e8af4d7d131f4f7921c79806`. GitHub Actions `45750785133`: Buildroot 2026.08.2 ARMv6 **BASE_ONLY_NOT_HOTSPOT**, `.img.xz` de **49.381.360 bytes**. Não é imagem operacional de hotspot.
- Margem matemática restante da base mínima: **30.618.640 bytes** (limite decimal = 80.000.000 bytes).
- Medição isolada adicional: `2pnyd` V2 TEST-2 recompilado para ARMv6, `go test` PASS e ELF ARM32 PASS no run `45789276902`: **7.012.536 bytes** sem compressão, **2.080.152 bytes** com XZ. Não está instalado na imagem mínima; somar tamanhos compactados de peças isoladas **não** substitui medir o conjunto final.
- Arquivos do painel V2 na árvore Git: **216.562 bytes sem compressão** (16 arquivos de origem; o stager instala 15 destinos). Teste de preparação estática: PASS.
- Após a medição isolada do `2pnyd`, a margem aritmética aproximada é **28.538.488 bytes**, ANTES dos gateways, display, managers, bibliotecas, configs, Helix, expansão e possíveis diferenças de compressão. **Não é tamanho final verificado**.
- `ci/v2-full-artifact-gate.py` rejeita imagens incompletas mesmo quando XZ está íntegro e abaixo de 80 MB; CI `45789276902` confirmou `V2_FULL_GATE_FAIL_CLOSED_PASS`. 
- O cumprimento da meta após integrar **todos** os componentes **não foi comprovado**.
- Interface V2 aprovada como fonte de UI em `panel/`, commit do HEAD da branch de UI `21fc9bd5cf4374ea507893e6630e322b2957f5b0`. Não inferir que API da UI está implementada por existir botão.
- Preservar o baseline de Nextion ON7LDS informado em `docs/PU2PNY-OS_UI_CONTRACT.md` (DISPLAY-041 / 5.00.002); não gravar HMI automaticamente nem trocar writer.
- START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX não foram encontrados sob esses nomes no snapshot V2; `docs/V2_MINIMAL_ACCEPTANCE.md` e contrato de UI são referências disponíveis. Nunca inventar PASS físico.

## Matriz de integração (status real)
| Bloco | Estado no Buildroot mínimo | Exigência |
|---|---|---|
| Kernel/boot ARMv6, systemd, Python e utilitários de rede | Base gerada; boot no HW não verificado | Confirmar boot e módulos |
| Painel V2 PT/EN/ES | Painel e binário empacotados juntos no overlay ARMv6, verificados em SW | Validar rotas no sistema inicializado, incluindo assistente e páginas auxiliares |
| 2pnyd/Go/API e persistência | ARMv6 compilado e empacotado; serviço ainda desativado no boot | Integrar dependências do serviço, persistência e validar API/estado real |
| MMDVMHost + modem e RF | Não integrado | Compilar compatível e preservar DMR/D-Star/YSF |
| DMR, D-Star, YSF, P25, NXDN, POCSAG | Não integrados | Gateways reais; ativação sob demanda, sem alegar RF PASS |
| Wi-Fi/AP/STA/Ethernet/mDNS, backup de 2 redes | Pacotes Linux presentes; managers PU2PNY ainda ausentes | Testar rollback e handoff |
| Nextion/ON7LDS, OLED, LCD/TFT | Não integrado | Preservar driver único, sem flash |
| APRS/DPRS, Direct/P2P e Histórico | Fontes/rotas existentes; serviços não integrados | Recursos de backend, testes, estado não fictício |
| Helix | Não integrado | OFF por padrão; AMBE apenas com backend licenciado validado |
| Atualização, backup, recuperação, segurança | Não integrados | Gates de backup/rollback e dados sensíveis |

## Regra para liberar release
1. Jamais renomear o Buildroot mínimo como imagem V2 completa.
2. Migrar as dependências e serviços para Buildroot com pacotes/binários realmente compatíveis com o ABI, evitando copiar executáveis Debian sem validar loader/bibliotecas.
3. Integrar todos os componentes e testar SW/VPS/CI; verificar `.img.xz` real por `stat`, `xz -t`, SHA-256 e montagem. **Tamanho <= 80.000.000 bytes em cada arquitetura**.
4. Se faltar qualquer componente essencial, funcionalidade ou teste de integridade, não publicar release completa.
5. ARM32 e ARM64 são imagens independentes. Nextion, RF, modem e display físico ficam como HW PENDENTE até evidência.
6. O novo relatório em `runtime/v2/full-report.go` exporta protocolo conhecido, estados de serviços e portas UDP locais. A release TEST-2 existente ainda inclui o relatório antigo, que pode expor credenciais. Não compartilhar exportações brutas daquela imagem.

## Integração nesta branch

- `ci/stage-v2-arm32.sh` prepara um overlay com as 15 páginas e arquivos estáticos do painel, o binário ARMv6 de 2pnyd e a unidade systemd. No build de integração, a unidade do painel é substituída pela original do TEST-2, com as restrições systemd preservadas. O build Buildroot com `--integration` compara os arquivos empacotados aos do overlay, verifica os binários MMDVM/Nextion e mede o conjunto com as dependências de rede, sem publicar imagem.
- Validado localmente com Go 1.24.9: `go test`, executável estático ELF ARM32, `GOARM=6`, teste do overlay e rejeição de imagem incompleta. Daemon novo: **7.012.536 bytes**, **2.079.236 bytes** com XZ. O total da imagem continua sem comprovação.
- O próximo ponto de integração é migrar o primeiro acesso e rede para a base Buildroot. Portar o gerenciador de Wi-Fi e as dependências de AP/STA e DHCP, integrar o assistente e validar duas redes com rollback antes de ativar o serviço do painel no boot. Em seguida, integrar RF e os gateways sem alterar o comportamento aprovado, displays e serviços restantes conforme a matriz.
- A última TEST-2 foi baixada e conferida: XZ íntegro, 729.802.744 bytes, SHA-256 `966d9d502508d4254712b89cdc57e30e5c48d57b544134667827e2af5c166261`.

## Migração dos binários de rádio e display

- A imagem TEST-2 publicada foi inspecionada em leitura. O sistema ext4 passou no `e2fsck -fn`. Os arquivos de procedência da imagem identificam MMDVM-Host em `590c531391dfd3146073afbc3956f70d42c62a46` e MMDVM-Display em `96a0705d818c4234960a61dd2837e32f9450f811`. O NextionDriver segue o commit `03b904270c9cb54f720d71753fc209afb1d9598f` e a etapa de endurecimento já usada pelo projeto.
- `buildroot/` fornece pacotes para recompilar os três binários na base leve. A toolchain Bootlin do Pi Zero W produziu localmente ELF ARM32/v6KZ para os três. O teste local de link de MMDVM-Host/Display usou a biblioteca MQTT da TEST-2 e os headers do Buildroot. O CI dos pacotes verifica o link com a própria biblioteca do Buildroot.
- O NextionDriver compilado preserva a porta virtual exclusiva em `/run/2pny-nextiondriver/ttyNextionDriver`. Os pacotes não ativam serviços, não alteram a configuração de RF e não gravam HMI/TFT.
- Na imagem TEST-2, `2pny-network-core.service` e `2pny-network-manager.service` dependem de NetworkManager. A base mínima ainda não inclui NetworkManager e o serviço gerenciador também requer `2pny-eventd`. A migração precisa portar esses componentes com seus estados e testar o comportamento de Wi-Fi/AP, em particular `nmcli`, `flock`, `rfkill`, regras de encaminhamento e os caminhos de firmware. O CI de software não valida RF, UART, rede sem fio física ou a tela.

- `ci/v2-arm32-integration.fragment` seleciona NetworkManager/nmcli, D-Bus do wpa_supplicant, Avahi, DHCP do dnsmasq, rfkill, flock e iptables junto aos três pacotes MMDVM/Nextion. Esses pacotes são dependências da migração; os scripts, configurações e serviços PU2PNY de rede e rádio ainda precisam ser integrados e validados.

## Baseline aprovado e geração da imagem leve

- O runtime do TEST-2 agora entra na compilação de integração a partir da imagem de referência com SHA-256 fixo, lida sem gravações. O overlay leva assistente, scripts, unidades e gateways ARMv6. O backend usa a revisão sanitizada. A etapa de migração não importa perfis, senhas ou estado do usuário.
- As unidades de rede, painel e RF ainda precisam de validação de boot como conjunto. A imagem de integração conserva a classificação de build; a aprovação física do TEST-2 não se transfere à base Buildroot.
- No TEST-2, o Helix usava ARMv7. O mesmo código de referência `b71a5fccd6371a88284866510000302f0126d565` agora é compilado para ARMv6. Passaram 47 testes de software e o autoteste do executável no QEMU com CPU ARM1176. Os modos permanecem desativados por padrão. A integração com hardware e com o rádio segue pendente.

- Na medição local do TEST-2, a cópia dos blocos alocados por `e2image -ra`, preservando MBR e partição de boot, gerou XZ íntegro de **584.222.128 bytes**. A limpeza de blocos livres, sem mexer nos arquivos, não atinge 80 MB. O overlay aprovado armazenou **642 arquivos**, cerca de **30 MiB** antes da compactação.

- A imagem de integração ativa as unidades originais de primeiro acesso, Wi-Fi e painel. Hostapd e dnsmasq continuam sob o gerenciador PU2PNY, com as unidades independentes bloqueadas. O MMDVM entra na lista de boot com a condição original de RF configurado. Gateways continuam dependentes dos perfis e o display depende da detecção.
- Em teste local ARM1176, o carregador iniciou a resolução de dependências dos seis gateways com a glibc Bootlin e as bibliotecas MQTT/TLS da referência. A verificação usa somente o carregador ELF e não inicia transmissão ou conexão de rádio. O CI repete a verificação com as bibliotecas da imagem Buildroot.

- A integração inclui conta de serviço `mmdvm`, grupos de acesso serial/I²C, fonte OLED, Pillow com FreeType, SMBus compatível e MQTT limitado a localhost. Esses ajustes são do sistema leve. O boot com modem, a persistência após reiniciar e a operação de rádio ainda não foram verificados nesta imagem.

- O CI confere o arquivo XZ contra o cartão gerado, verifica FAT e ext4, remonta a raiz em leitura e confere o painel, as unidades de boot, a conta MMDVM e a ausência de estado de provisionamento. Se passar com até 80 MB, guarda o build e o SHA no Actions para validação de engenharia. A publicação da imagem destinada a instalação permanece condicionada à validação do firmware.
