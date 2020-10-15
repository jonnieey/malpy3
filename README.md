## Description

`malpy3` is a command-line client for [MyAnimeList](https://myanimelist.net/) via  [OpenBeta API](https://api.myanimelist.net/v2)

[See more on [offical docs]( https://myanimelist.net/apiconfig/references/api/v2)]

This project is an unofficial fork of [ryukinix/mal](https://github.com/ryukinix/mal) [ARCHIVED].

![demo](demos/demo1.gif)
![demo](demos/demo2.gif)

## Features
- Search your anime/manga list.
- Fetch your anime/manga list.
- List animes/manga by their status (e.g. `watching/reading`).
- Increment or decrement episode/chapter watch or read count.
- Add anime/manga to your `Plan To Watch or Plan To Read` list.
- Edit anime metadata (currently `tags`, `status` and `score`) using your favorite text editor.
- Print your MAL stats


## Requirements

- python3.6 or above

- [Poetry](https://python-poetry.org/docs/)


## Installation

### Create MAL API Client

`malpy3` requires MAL API client.
    - [Create MAL API Client](https://myanimelist.net/apiconfig/create)

There is a great guide on how  to create one.
    - [Guide to create MAL API Client](https://myanimelist.net/blog.php?eid=835707)


### Manual Installation

Clone this project and inside it run:

    make install

- Recommended: Use virtualenv


## Authenticating

`malpy3` requires your credentials in order to access your anime list.
On it's first call to any valid command, it will ask for your
username and password.

It will authenticate it with MAL and returns tokens which are
stored in XDG_CONFIG_HOME path.  (on linux ``~/.config/mal/myanimelist.toml``).


## Using The Interface

When ``malpy3`` is executed without any arguments a help message is
displayed:


    usage: mal [-h] [-v] 
        {search,list,filter,increase,inc,decrease,dec,login,config,drop,stats,add,edit} ...

    MyAnimeList command line client.

    positional arguments:
      {search,list,filter,increase,inc,decrease,dec,login,config,drop,stats,add,edit}
                            commands
        search              search an anime/manga globally on MAL
        list                list anime/manga in users list using status
        filter              find anime/manga in users list
        increase (inc)      decrease anime/manga episode or chapter progress (default: +1)
        decrease (dec)      decrease anime/manga episode or chapter progress (default: -1)
        login               login to MAL and save login credentials
        config              Print current config file and its path
        drop                Put a selected anime/manga on drop list
        stats               Show user's anime watch stats
        add                 add an anime/manga to the list
        edit                edit anime/manga

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show the version of malpy3

You can also use the ``-h`` or ``--help`` options on ``malpy3`` or any of
its subcommands to see specific help messages.

### Examples

    Search for anime with limit on results.
    $ mal search "Hajime no ippo" --limit 5

    Search for manga with extra information.
    $ mal search "Hajime no ippo" -c manga --extend

    show anime that are on hold list
    $ mal list 'on hold'

    show manga that are on plan to read list
    $ mal list -c manga 'plan to read'

    increase anime episodes watched by 3
    $ mal inc 'terra formars' 3

    search anime user's profile
    $ mal filter 'hellsing'

    show user's anime stats
    $ mal stats

