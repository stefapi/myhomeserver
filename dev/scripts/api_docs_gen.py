import json

import re
from pathlib import Path
from myeasyserver.webserver import app
from myeasyserver.core.settings import AppDirectories, EnumSettings

"""Script to export the ReDoc documentation page into a standalone HTML file."""

HTML_TEMPLATE = """<!-- Custom HTML site displayed as the Home chapter -->

<style>
    body {
        margin: 0;
        padding: 0;
    }
</style>


<div id="redoc-container"></div>
<script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"> </script>
<script>
    var spec = MY_SPECIFIC_TEXT;
    Redoc.init(spec, {}, document.getElementById("redoc-container"));
</script>

"""

appdirs = AppDirectories(EnumSettings.Debug)
HTML_PATH = Path(appdirs.DATA_DIR).parent.parent.joinpath("docs/api.html")


def generate_api_docs(my_app):
    with open(HTML_PATH, "w") as fd:
        text = HTML_TEMPLATE.replace("MY_SPECIFIC_TEXT", json.dumps(my_app.openapi()))
        fd.write(text)


if __name__ == "__main__":
    generate_api_docs(app)
