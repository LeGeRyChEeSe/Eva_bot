<h1 align='center'>EvaBot Discord</h1>
<p align="center">
<img src="https://github.com/LeGeRyChEeSe/Eva_bot/blob/main/assets/Images/Alpha-afterH.ab8f1852.png?raw=true" align="center" height=205 alt="evabot" />
</p>
<p align="center">
<img src='https://visitor-badge.laobi.icu/badge?page_id=LeGeRyChEeSe.evabot'>
<a href="https://github.com/LeGeRyChEeSe/evabot/stargazers">
<img src="https://img.shields.io/github/stars/LeGeRyChEeSe/evabot" alt="Stars"/>
</a>
<a href="https://github.com/LeGeRyChEeSe/evabot/issues">
<img src="https://img.shields.io/github/issues/LeGeRyChEeSe/evabot" alt="Issues"/>
</a>

<p align="center">
This is the unofficial original Discord Bot of <a href="https://www.eva.gg/">EVA</a>.
It's made for getting stats and previous games from a Player in one command easily. There is also more features like getting booking sessions, and a custom players ranking. Since this project has been published, feel free to give your help to this project if you want, there is many issues actually that I cannot fix yet ! Knowns issues are mentionned below.
<p align="center">

## Table of Contents
- [Installation](#installation)
- [Running](#running)
    - [Local](#local-run-from-source)
    - [Docker](#docker)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Install [Python](https://www.python.org/downloads/) if not already installed.

- Install Eva_bot from the source
    ```bash
    git clone https://github.com/LeGeRyChEeSe/Eva_bot.git && cd Eva_bot && pip install -r requirements.txt
    ```

## Running

1. Create a `.env` file.

2. Copy and replace the values of these Environment Variables into the `.env` file
    ```python
    TOKEN='DISCORD_API_TOKEN'
    HOST_DB='HOST_DATABASE'
    USER_DB='USER_DATABASE'
    PASSWD_DB='PASSWORD_DATABASE'
    DB='DATABASE'
    ```
### Local run (from source)
```bash
python main.py
```
**Don't forget to let your terminal open or the bot will just stop.**
### Docker

```bash
docker compose up -d --build
```

## Contributing

Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit your Changes (`git commit -m 'Add some NewFeature'`)
4. Push to the Branch (`git push origin feature/NewFeature`)
5. Open a Pull Request


*Thanks to every [contributors](https://github.com/LeGeRyChEeSe/Eva_bot/graphs/contributors) who have contributed in this project.*

## License

Distributed under the MIT License. See [LICENSE](https://github.com/LeGeRyChEeSe/Eva_bot/blob/main/LICENSE) for more information.

-----
Author/Maintainer: [Garoh](https://github.com/LeGeRyChEeSe/) | Discord: GarohRL#4449
