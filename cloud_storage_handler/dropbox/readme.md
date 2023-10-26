# Purpose

This handler simply manage your files with dropbox by using your own dropbox OAuth client.
To be able to use this module from colaboratory notebook, it just prompt URL.

# How to setup

This module doesn't provide OAuth client credentials. You need to provide them by creating your own dropbox client.

1. Access [developer portal](https://www.dropbox.com/developers), then click create app
1. choose "Scoped access", "App folder". Then input your app name. Note that it becomes yoru folder name in dropbox.
1. Add permissions, files.content.write and rea
1. Add redirect URL. Basically it is "http://localhost" for local dev purpose
1. copy client key (it is called client_id in this module) and redirect URL

# How to use

By specifying client_id and redirect_url you obtained on "How to setup", you can initialize the module

```
from cloud_storage_handler import DropboxHandler

handler = DropboxHanlder(client_id, redirect_url)

```

Then authenticate yourself

```

handler.authenticate()

```

It prompots URL and input field. By accessing the URL with your browser, you can obtain temporal code for proceeding the authentication. Then input the code to input filed prmprted.
