==============================================
o365update.pyの使い方 - 概要
==============================================

.. contents:: 目次

利用手順の概要
----------------------
* 一緒に配布されている “o365update.py”の37～65行目をユーザ様のニーズに応じて変更
* BIG-IPのローカルディスク上に配置
* 上記PythonプログラムをcronまたはiCallで定期実行

o365update.pyの機能
----------------------

1.	BIG-IPがActiveかStandbyかを判定。Standbyの場合は、それ以上何もせずにプログラムを終了
2. 	Microsoft社のWebサイト（2019年7月現在 “endpoints.office.com"）から現在のMS365 Endpointリストのバージョンを確認
3.	既にBIG-IP上にあるリストと同じバージョンであれば、それ以上何もせずにプログラムを終了
4.	Microsoft社のWebサイトにより新しい情報がある場合はO365 EndpointリストをJSON形式で取得
5.	ユーザ設定に従って対象としたいMSアプリケーションを絞り込み

    *   Common
    *   Exchange
    *   Skype
    *   Sharepoint
    *   Yammer

5.	ユーザ設定に従って下記3パターンのURL、IPv4アドレス、IPv6アドレスをそれぞれ抽出

    *   全て
    *   Express Routeを通すもの、
    *   Express Routeを通さないもの

6.  URLのリストに対して

    1.  "*"を含むホスト名またはサブドメインは一番近い右側の “.”の手前まで削除
    2.  全て小文字に変更
    3.  並べ変えた後に重複するレコードを削除
    4.  BIG-IPにインポートするためのフォーマットに整形します。
    5.  上記の整形済みリストを「(ユーザ定義のData Group名) 」+ 「_object」という名称のData Group File にインポートします。当該Data Group Fileが存在しない場合は自動で新規作成します。

7.	IPのリストに対して

    1.  IPv4, IPv6を仕分け
    2.  /xxとサブネット長の記述のあるアドレスの頭に“network ”を付記。サブネット長の記述が無い場合は“host “を付記
    3.  BIG-IPにインポートするためのフォーマットに整形
    4.  上記の整形済みリストを「(ユーザ定義のData Group名) 」+ 「_object」という名称のData Group File にインポートします。当該Data Group Fileが存在しない場合は自動で新規作成します。

8.	上記Data Group Fileに対応するData Groupが存在しない場合は新規に作成します。
9.	ConfigをSaveし
10.	Config-Syncを行います






