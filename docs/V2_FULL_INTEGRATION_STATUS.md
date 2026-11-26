# PU2PNY-V2 — integração completa e limite de 80 MB

**Situação em 26/11/2026:** EM DESENVOLVIMENTO; imagem V2 completa de até 80.000.000 bytes **NÃO ENTREGUE**.

## Baselines e evidência verificadas
- Repositório: `PU2PNY/PU2PNY-V2`.
- Branch TEST-2: `build/v2-test-2`, commit `34e6bab0e1b99e95c1a4b79c11198d8d89f9b90e`.
- Última publicação V2: `pu2pny-v2-test-2`. Arquivo ARM32 `pu2pny-32-v2-test-2.img.xz` tem **729.802.744 bytes**, embora validado no CI; não atingiu 80 MB. RF/display físico NÃO VERIFICADO na release.
- Branch mínima: `build/v2-minimal-80mb`, commit `ec944beca0b81c63e8af4d7d131f4f7921c79806`. GitHub Actions `45750785133`: Buildroot 2026.08.2 ARMv6 **BASE_ONLY_NOT_HOTSPOT**, `.img.xz` de **49.381.360 bytes**. Não é imagem operacional de hotspot.
- Margem matemática restante: **30.618.640 bytes** (limite decimal = 80.000.000 bytes). O cumprimento da meta após integrar os componentes **não foi comprovado**.
- Interface V2 aprovada como fonte de UI em `panel/`, commit do HEAD da branch de UI `21fc9bd5cf4374ea507893e6630e322b2957f5b0`. Não inferir que API da UI está implementada por existir botão.
- Preservar o baseline de Nextion ON7LDS informado em `docs/PU2PNY-OS_UI_CONTRACT.md` (DISPLAY-041 / 5.00.002); não gravar HMI automaticamente nem trocar writer.
- START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX não foram encontrados sob esses nomes no snapshot V2; `docs/V2_MINIMAL_ACCEPTANCE.md` e contrato de UI são referências disponíveis. Nunca inventar PASS físico.

## Matriz de integração (status real)
| Bloco | Estado no Buildroot mínimo | Exigência |
|---|---|---|
| Kernel/boot ARMv6, systemd, Python e utilitários de rede | Base gerada; boot no HW não verificado | Confirmar boot e módulos |
| Painel V2 PT/EN/ES | Fontes disponíveis; *stager* isolado adicionado | Integrar ao daemon e testar todas as rotas/APIs |
| 2pnyd/Go/API e persistência | Não integrado à base mínima | Compilar ARMv6/ARM64 e validar endpoints/estado real |
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
6. Evitar incluir o gerador atual de relatório TEST-2 sem sanitização: `ci/prepare-v2-test-2-backend.py` contém `fileSec("CONFIG (config.json)", configFile)` e logs brutos potencialmente sensíveis. Deve ser corrigido e testado antes de portá-lo.

## Mudança nesta branch de integração
`ci/v2-panel-overlay.py` prepara a interface V2 para um rootfs limpo, sem depender da imagem Debian de 729 MB. **Não inicia serviços, não contém backend nem é uma imagem completa.** Trabalho restante deve permanecer documentado, sem promessas de status PASS.
