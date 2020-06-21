.. You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ansible for BIG-IP サンプルコード
==============================================

BIG-IPをAnsibleで設定する際の、サンプルコード (Ansible Playbook等)を公開しています。

はじめに
--------------------------------
ここで紹介している設定ファイル等は、F5社が公式にサポートするものではありません。


あくまでも検証等のサンプル用として、ご利用ください。

ディレクトリの説明
--------------------------------
階層構造の説明は以下の通りです。

変数等につきましては、使用する環境に合わせて変更の上、ご利用ください。

- config: iRules等の設定ファイルを格納するディレクトリ
- inventory: グループやホストに関する変数等を格納するディレクトリ
- playbook: Ansible Playbookを格納するディレクトリで、以下のplaybookを公開しています。

  - as3_comfig_sample.yml: AS3を使ってBIG-IPの基本的な設定を実行する、Playbookのサンプル
  - bigip_config_sample.yml: BIG-IPの基本的な設定を実行する、Playbookのサンプル
  - bigip_ha_config_sample.yml: 工場出荷時の2つのBIG-IPインスタンスから、HA (High Availability)構成を実現する、Playbookのサンプル

- template: AS3による設定時のテンプレート (Jinja2)を格納するディレクトリ