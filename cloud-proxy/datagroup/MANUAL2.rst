==============================================
o365update.pyの使い方 - 詳細
==============================================

.. contents:: 目次

1. オプション設定
=========================
o365update.pyの22~46行を必要に応じて変更してください

取得するデータの選択
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "項目", "デフォルト", "説明"
    :widths: 15, 10, 30

    use_url,1,"1= URLリストを取得・更新する, 0=しない"
    use_ipv4,0,"1= IPv4リストを取得・更新する, 0=しない"
    use_ipv6,0,"1= IPv6リストを取得・更新する, 0=しない"
    use_url_express_route,0,"1= URLリストを取得・更新する, 0=しない ※1"
    use_ipv4_express_route,0,"1= IPv4リストを取得・更新する, 0=しない ※1"
    use_ipv6_express_route,0,"1= URLリストを取得・更新する, 0=しない ※1"

※1 Express Routeを通す/通さない、の2つのデータグループを生成します

データ取得の対象とするアプリケーション(serviceArea)の選択
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "項目", "デフォルト", "説明"
    :widths: 15, 10, 40

    care_common,1,"1= “Common”を対象とする, 0=しない"
    care_exchange,1,"1= “Exchange”を対象とする, 0=しない"
    care_skype,1,"1= “Skype”を対象とする, 0=しない"
    care_sharepoint,1,"1= “Sharepoint”を対象とする, 0=しない"
    care_yammer,1,"1= “Yammer”を対象とする, 0=しない"

MSが配布するデータが更新されていなくてもBIG-IPへの更新を行うか
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "項目", "デフォルト", "説明"
    :widths: 15, 10, 30

    force_o365_record_refresh,0,"1=更新する, 0=しない"

* 導入時やテスト時の動作確認のため強制的に更新させたい場合に「１」をご利用ください

BIG-IP Data Groupの名称
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "項目", "デフォルト", "説明"
    :widths: 15, 10, 30

    dg_urls_to_bypass_all,ext_o365_url ※2,URL のリスト
    dg_urls_to_bypass_er_true,ext_o365_url_er_true,Express Routeを通すURLリスト
    dg_urls_to_bypass_er_none,ext_o365_url_er_none,Express Routeを通さないURLリスト
    dg_ip4s_to_bypass_all,ext_o365_ip4,IPv4のリスト
    dg_ip4s_to_bypass_er_true,ext_o365_ip4_er_true,Express Routeを通すIPv4のリスト
    dg_ip4s_to_bypass_er_none,ext_o365_ip4_er_none,Express Routeを通さないIPv4のリスト
    dg_ip6s_to_bypass_all,ext_o365_ip6,IPv6のリスト
    dg_ip6s_to_bypass_er_true,ext_o365_ip6_er_true,Express Routeを通すIPv6のリスト
    dg_ip6s_to_bypass_er_none,ext_o365_ip6_er_none,Express Routeを通さないIPv6のリスト

※2 別途配布されている設定ガイド（「BIG-IP LTM かんたんセットアップガイド(v12.1) Office365向けOutbound通信対策編」）の通りに用いる場合はデフォルト（"ext_o365_url"）のままで結構です

冗長構成関連
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "項目", "デフォルト", "説明"
    :widths: 15, 10, 30

    device_group_name, device-group1, "冗長構成の場合は必須です。冗長構成のため設定したDevice Group名称を与えます。Config Syncのために用いられます。"
    ha_config,1,"1= 冗長構成, 0=スタンドアロン"

ログ関連
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "項目", "デフォルト", "説明"
    :widths: 15, 10, 30

    log_level,1,0=ログ出力無し、1=通常レベル、2=詳細レベル
    log_dest_file,"""/var/log/o365_update""",ログ出力先のファイル名を指定します。デフォルトのままで特に問題ありません

*   ログレベルは通常は 1での利用を推奨します。テストや動作確認のためより詳細なログが必要な場合は2をご利用ください

2.  o365update.pyの配置
==============================================

| “o365update.py”をSCP等を用いてBIG-IPのローカルディスク上(例: /var/tmp/o365)に配置
| （“o365update.py”は実行時にいくつかファイルを生成するため、/var/tmp/o365などのフォルダを作成することをお勧めします）

3.  動作確認
==============================================

コマンドラインから
    # python /var/tmp/o365/o365update.py
と入力し、動作を確認します。別のターミナルを開き下記のようにログファイルを表示することで同時にログを確認できます。
    # tail -f /var/log/o365_update

（ログ出力先をデフォルト値から変更された場合は “/var/log/o365_update” の部分を適宜変更してください）

正常に動作すると

*	use_ipv4、use_ipv6のいずれかまたは両方を 1に設定していた場合

    ワークディレクトリ(デフォルト /var/tmp/o365)にo365_ip4.txt、o365_ip6.txtが生成されます。

*	use_urlを1に設定していた場合

    *   Local Traffic  ››  iRules : Data Group List　にData Groupが作成されます。dg_urls_to_bypass変数に設定した名称（デフォルト “ext_o365_url”）で作成されます。既に存在している場合は何もしません

    .. image:: ./pics/fig01.png

    *   System  ››  File Management : Data Group File List　にData Group Fileが作成されます。dg_urls_to_bypass変数に設定した名称（デフォルト “ext_o365_url”）の末尾に”_object”を追加した名称で作成されます。既に存在している場合は内容が上書きされます。下記スクリーンショット中の”VERSION”が上書きの都度カウントアップされます。

    Last Update Dateが変わっている事でも更新が確認できます。

    .. image:: ./pics/fig02.png

    上記のData Group File (例 “ext_o365_url_object”)をクリックすると内容が参照できます。

    .. image:: ./pics/fig03.png


*	use_url_express_route を１に設定していた場合
*	use_ipv4_express_route を１に設定していた場合
*	use_ipv6_express_route を１に設定していた場合

    それぞれに、Express Routeを通す用、通さない用のData Group FileおよびData Groupを作成・更新します

4.  cronの設定
==============================================

下記コマンドを打ちcrontabの編集モードに入る

.. code-block:: text

    # crontab –e

要件に応じて下記のように記述を追加。例は一時間おきの実行。o365update.pyのパスは実際に応じて適宜変更してください。

.. code-block:: text

    5 * * * * python /var/tmp/o365/o365update.py

保存終了後、下記コマンドを用いて変更が反映されていることを確認します。

.. code-block:: text

    | # crontab -l
    | # cron tab for root
    | 1-59/10 * * * * /usr/bin/diskmonitor
    | 0 \*/4 * * * /usr/bin/diskwearoutstat
    | 49 20 * * * /usr/bin/updatecheck -a
    | 49 20 11 * * /usr/bin/phonehome_activate
    | MAILTO=""
    | 20 * * * * /usr/bin/copy_rrd save
    | 5 * * * * python /var/tmp/o365update.sh


Microsoft社の下記サイトでは、エンドポイントリストの参照は１時間に１回に留めることが推奨されています。

    | `Office 365 IP アドレスと URL の Web サービス - Microsoft 365 Enterprise | Microsoft Docs`
    | https://docs.microsoft.com/ja-jp/microsoft-365/enterprise/microsoft-365-ip-web-service

5.  ログファイルをlogrotateの対象にする設定
========================================================================

ログはPythonプログラムのlog_dest_fileに指定したファイル
    log_dest_file = "/var/log/o365_update"

に書き込まれますが、長期間の運用ではログファイルのサイズが肥大することが考えられます。BIG-IPの他のログファイルと同様にlogrotateの対象に加えるには下記のように設定します。

以下のようにTMSHコマンドを打つと

.. code-block:: text

    (tmos)# edit /sys log-rotate all-properties

以下のようなeditモードに入ります

.. code-block:: text

    modify log-rotate {
        common-backlogs 24
        common-include none
        description none
        include none
        max-file-size 1024000
        mysql-include none
        syslog-include none
        tomcat-include none
        wa-include none
    }

“include none” の部分を下記のように編集します

.. code-block:: text

    modify log-rotate {
        common-backlogs 24
        common-include none
        description none
        include "/var/log/o365_update
        {
            compress
            missingok
            notifempty
            sharedscript
            postrotate
            endscript
        }"
        max-file-size 1024000
        mysql-include none
        syslog-include none
        tomcat-include none
        wa-include none
    }

":" "w" ":" "x"とキーを押して編集画面を抜け、下記プロンプトでyと入力して編集した内容を保存

.. code-block:: text

    # Save changes? (y/n/e) y

下記コマンドを入力し設定を保存します

.. code-block:: text

    (tmos)# save /sys config


関連情報
=====================

    * Office 365 の URL と IP アドレスの範囲 - Microsoft 365 Enterprise | Microsoft Docs https://docs.microsoft.com/ja-jp/microsoft-365/enterprise/urls-and-ip-address-ranges?view=o365-worldwide&WT.mc_id=email

