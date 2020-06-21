.. You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ansible for BIG-IP サンプルコード
==============================================

BIG-IPをAnsibleで設定する際の、サンプルファイル (Ansible Playbook等)を公開しています。

はじめに
--------------------------------
ここで紹介している設定ファイル等は、F5社が公式にサポートするものではありません。
検証等のサンプルとして、ご利用ください。

ディレクトリの説明
--------------------------------
階層構造の説明は以下の通りです。

- config: iRules等の設定ファイルを格納するディレクトリ
- inventory: グループやホストに関する変数等を格納するディレクトリ
- playbook: Ansible Playbookを格納するディレクトリ
- templates: AS3による設定時のテンプレート (Jinja2)を格納するディレクトリ