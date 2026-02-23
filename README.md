<!-- Language selector -->
<!-- Language selector -->
<p align="center">
  <a href="#en-us">🇺🇸 English</a> | 
  <a href="#pt-br">🇧🇷 Português</a>
</p>


---
---
<a id="en-us"></a>
# Epson Printers (SNMP) – Home Assistant Integration 🇺🇸

Custom Home Assistant integration to monitor **Epson printers via SNMP**.

The goal is to provide reliable printer information in a simple and seamless way, fully integrated into the Home Assistant interface.

---

## ✨ Features

- Epson printer monitoring via SNMP
- Automatic detection of supported models
- Page counters
- Ink level monitoring
- Device information integrated into Home Assistant
- Fully native Home Assistant UI
- Multi-language support (English and Portuguese)

---

## 📊 Available data

### Page counters

The integration exposes two main counters:

- **Total pages**  
  Total number of pages printed during the printer’s lifetime

- **Pages since power on**  
  Number of pages printed since the printer was last powered on

---

### Ink levels

- Ink level monitoring per cartridge
- Percentage values when available
- Proper handling of unknown or unavailable values

---

### Device information

Information such as **firmware version**, model, and manufacturer are shown directly in the **Device details** view, keeping the sensor list clean and focused.

---

## ⚙️ Configuration

Configuration is done entirely through the Home Assistant UI:

- Printer host
- Device name
- SNMP community
- SNMP version
- Update interval

No manual file editing is required after installation.

---

## 🖨️ Supported printers

| Model | Status |
|------|-------|
| Epson L3250 | ✅ Supported |

Additional models may be added in the future.

---

## 📦 Installation

### Manual installation

1. Copy the `epson_snmp` folder into:
   ```
   /config/custom_components/
   ```
2. Restart Home Assistant
3. Add the integration via the UI

---

## 📄 License

MIT License

---
---
<a id="pt-br"></a>
# Epson Printers (SNMP) – Integração para Home Assistant 🇧🇷

Integração customizada do Home Assistant para monitorar **impressoras Epson via SNMP**.

O objetivo é fornecer informações confiáveis da impressora de forma simples, direta e integrada à interface do Home Assistant.

---

## ✨ Funcionalidades

- Monitoramento de impressoras Epson via SNMP
- Detecção automática do modelo compatível
- Contadores de páginas impressas
- Monitoramento de níveis de tinta
- Informações do dispositivo integradas ao Home Assistant
- Interface totalmente integrada à UI do Home Assistant
- Suporte a múltiplos idiomas (Português e Inglês)

---

## 📊 Informações disponíveis

### Contadores de páginas

A integração expõe dois contadores principais:

- **Total de páginas**  
  Total de páginas impressas ao longo da vida útil da impressora

- **Páginas desde a última ligação**  
  Quantidade de páginas impressas desde que a impressora foi ligada pela última vez

---

### Níveis de tinta

- Exibição dos níveis de tinta por cartucho
- Valores percentuais quando disponíveis
- Estados desconhecidos são tratados corretamente quando a impressora não informa dados válidos

---

### Informações do dispositivo

Algumas informações, como **versão de firmware**, modelo e fabricante, são exibidas diretamente nos **detalhes do dispositivo** no Home Assistant, mantendo a interface limpa e sem sensores desnecessários.

---

## ⚙️ Configuração

A configuração é feita inteiramente pela interface do Home Assistant:

- Endereço da impressora
- Nome do dispositivo
- Comunidade SNMP
- Versão do protocolo SNMP
- Intervalo de atualização

Não é necessário editar arquivos manualmente após a instalação.

---

## 🖨️ Impressoras compatíveis

| Modelo | Status |
|------|-------|
| Epson L3250 | ✅ Suportado |

Outros modelos podem ser adicionados futuramente.

---

## 📦 Instalação

### Instalação manual

1. Copie a pasta `epson_snmp` para:
   ```
   /config/custom_components/
   ```
2. Reinicie o Home Assistant
3. Adicione a integração pela interface gráfica

---

## 📄 Licença

MIT License

