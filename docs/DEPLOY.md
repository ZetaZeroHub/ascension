# 静态部署

网站无运行时服务与数据库，只需发布 `site/`。Git 仓库中的源文件和默认的轻量网站媒体包共同组成站点。`fetch_media.py` 不带 `--inputs`：原始输入图不会下载到服务器。`site/` 中仅有一条完整 MV，不含模型权重、历史视频或独立音轨。

```sh
git clone https://github.com/ZetaZeroHub/ascension.git
cd ascension
python3 scripts/fetch_media.py
python3 scripts/verify_public.py
```

将 `site/` 放到自己的静态站点根目录。使用 Nginx 时参考 `deploy/nginx.conf`，按自己的站点路径修改 `root`，保留已有虚拟主机，先 `nginx -t` 再重载。

推荐版本化目录：`releases/<commit>/site`，由 `current` 符号链接指向当前版本。切换前检查影片、图稿和工作流文件完整性；回滚时将链接切回先前版本。只有首次部署且原本无独立虚拟主机时，移除新建的该域名配置才是回滚方式。

本项目域名采用现有 CDN HTTPS 入口和 Nginx 源站架构；模板不含证书或任何凭据。不要把本地设计预览的文件系统代理部署到公网。

验收：主页 200、静态文件 200、视频 Range 请求 206、不存在文件 404、隐藏文件不公开、中文/英文切换、手机布局、原稿下拉选择与实际播放。对历史归档页面不承诺全部已翻译为英文。
