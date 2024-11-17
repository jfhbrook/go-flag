#!/usr/bin/env bash

UV_PUBLISH_TOKEN="$(op item get 'PyPI' --fields 'API Token' --reveal)"

export UV_PUBLISH_TOKEN

uv publish
