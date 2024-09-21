# VidiLex (BETA)

Bem-vindo ao **VidiLex**, uma ferramenta automática de conversão e compressão de vídeos, projetada para facilitar o trabalho com arquivos de vídeo armazenados no Google Drive. O objetivo do **VidiLex** é fornecer uma solução simples e eficiente para conversão de vídeos, com integração direta ao Google Drive.

## Funcionalidades

- **Download automático de vídeos do Google Drive**: Basta fornecer o ID da pasta do Google Drive e o VidiLex cuidará do resto.
- **Conversão e compressão de vídeos**: Converte vídeos em diferentes resoluções (120p até 2160p) para o formato desejado, com suporte para o codec WMV2.
- **Monitoramento contínuo**: O sistema faz verificações contínuas por novos vídeos na pasta do Google Drive especificada.
- **Interface rica**: Utiliza a biblioteca `rich` para exibir barras de progresso e informações de status de forma clara e visualmente atraente.
- **SHA-256 para evitar duplicação**: O sistema processa cada vídeo uma única vez, evitando duplicações.

## Requisitos

Antes de iniciar, certifique-se de ter os seguintes requisitos instalados:

- Python 3.7 ou superior
- Google Drive API configurada
- Bibliotecas Python necessárias (veja [Instalação](#instalação))

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/vidilex.git
cd vidilex
```

2. Crie um ambiente virtual e ative-o:

```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate  # Windows
```

3. Instale as dependências necessárias:

- Crie um projeto no Google Cloud Console.
- Ative a Google Drive API.
- Baixe o arquivo de credenciais `credentials.json` e coloque-o na raiz do projeto.

## Uso

1. Execute o VidiLex para começar a monitorar a pasta do Google Drive:

```bash
python main.py
```

2. Quando solicitado, insira o ID da pasta do Google Drive que contém os vídeos que deseja processar.

3. O sistema baixará automaticamente os vídeos da pasta, converterá e comprimirá os vídeos conforme a configuração, e salvará os arquivos convertidos na pasta local `videos`.

## Configuração
### Resolução de Vídeo

O VidiLex suporta várias resoluções de vídeo. Para ajustar a resolução, altere o parâmetro `video_quality` ao instanciar o VidiLex:

- `120p`
- `240p`
- `360p`
- `480p`
- `720p`
- `1080p`
- `1440p`
- `2160p`

Exemplo:

```bash
vidilex = VidiLex(output_format="asf", video_quality="720p")
```

### Formato de Saída

Atualmente, o VidiLex suporta o formato de saída WMV. Você pode alterar o formato de saída ao instanciar o VidiLex.

## Contribuição

Se você deseja contribuir com o projeto, siga os passos:

1. Fork este repositório.
2. Crie um branch para sua feature (`git checkout -b feature/MinhaFeature`).
3. Faça commit das suas mudanças (`git commit -m 'Adiciona MinhaFeature'`).
4. Dê push no branch (`git push origin feature/MinhaFeature`).
5. Abra um Pull Request.

## Aviso

Este sistema está em fase de desenvolvimento (BETA), e pode apresentar instabilidades. Pedimos paciência e feedback para que possamos melhorar o VidiLex continuamente.

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](./LICENSE.md) para mais informações.