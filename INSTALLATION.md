# Guia de Instalação - Baru Validator QGIS Plugin

## Instalação Rápida

### Pré-requisitos
- QGIS 3.0 ou superior
- Python 3.6+
- Acesso à pasta de plugins do QGIS

### Passo 1: Localizar a pasta de plugins do QGIS

#### Windows
```
C:\Users\<seu_usuario>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
```

#### Linux
```
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins
```

#### macOS
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins
```

### Passo 2: Copiar o plugin

1. Copie a pasta `baru_validator` para a pasta de plugins do QGIS
2. Certifique-se de que a estrutura está correta:
   ```
   plugins/
   └── baru_validator/
       ├── __init__.py
       ├── baru_validator.py
       ├── validation_metrics.py
       ├── confusion_matrix.py
       ├── report_generator.py
       ├── metadata.txt
       ├── LICENSE
       ├── icons/
       │   └── baru_icon.png
       └── temp/
   ```

### Passo 3: Instalar dependências

Abra o terminal/prompt de comando do QGIS e execute:

```bash
pip install numpy pandas scikit-learn shapely
```

Ou, se estiver usando o Python do QGIS diretamente:

#### Windows (OSGeo4W Shell)
```
python -m pip install numpy pandas scikit-learn shapely
```

#### Linux/macOS
```
python3 -m pip install numpy pandas scikit-learn shapely
```

**Nota para usuários Linux:** Se encontrar o erro "This environment is externally managed", tente instalar via gerenciador de pacotes do sistema (ex: `sudo apt install python3-numpy python3-pandas python3-sklearn python3-shapely`) ou use um ambiente virtual se estiver desenvolvendo.

### Passo 4: Reiniciar o QGIS

Feche e reabra o QGIS completamente.

### Passo 5: Ativar o plugin

1. Abra QGIS
2. Vá para **Plugins → Gerenciar e Instalar Plugins**
3. Procure por "Baru Validator"
4. Marque a caixa ao lado do plugin para ativá-lo
5. Clique em **Fechar**

### Passo 6: Verificar a instalação

Se a instalação foi bem-sucedida, você verá:
- Um novo ícone na barra de ferramentas do QGIS (ícone de árvore com "BARU")
- Um novo menu **Baru Validator** no menu **Plugins**

## Solução de Problemas

### O plugin não aparece em "Gerenciar Plugins"

1. Verifique se a pasta `baru_validator` está no local correto
2. Certifique-se de que o arquivo `metadata.txt` está presente
3. Verifique se o arquivo `__init__.py` está correto
4. Verifique o log do QGIS para erros:
   - Vá para **Plugins → Python Console**
   - Procure por mensagens de erro relacionadas ao Baru Validator

### "ModuleNotFoundError: No module named 'sklearn'"

As dependências não foram instaladas corretamente. Execute novamente:

```bash
pip install scikit-learn numpy pandas shapely
```

### O plugin carrega mas não funciona

1. Verifique se todas as dependências estão instaladas
2. Abra o **Python Console** do QGIS e tente importar:
   ```python
   from baru_validator.validation_metrics import ValidationMetrics
   ```
3. Se houver erro, verifique a mensagem e corrija o problema

### Geração de Relatórios

O plugin agora gera relatórios em formato **HTML** de alta qualidade, que podem ser visualizados em qualquer navegador e impressos como PDF. Isso elimina a necessidade da biblioteca externa `reportlab`, facilitando a instalação em sistemas Linux.

## Desinstalação

Para desinstalar o plugin:

1. Vá para **Plugins → Gerenciar e Instalar Plugins**
2. Procure por "Baru Validator"
3. Desmarque a caixa para desativar
4. Clique em **Desinstalar Plugin** (se disponível) ou simplesmente delete a pasta `baru_validator`
5. Reinicie o QGIS

## Suporte

Se encontrar problemas durante a instalação:

1. Verifique se está usando QGIS 3.0 ou superior
2. Consulte o README.md para mais informações
3. Verifique o log do QGIS para mensagens de erro detalhadas
4. Entre em contato com support@manus.im

## Próximos Passos

Após a instalação bem-sucedida, consulte o README.md para instruções de uso do plugin.
