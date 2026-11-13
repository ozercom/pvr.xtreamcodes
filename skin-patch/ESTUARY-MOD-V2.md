# Estuary MOD V2 quick-nav button

This is an optional skin-side hook for the separate channel browser add-on.

1. Install `plugin.video.xtreamcodes.browser-0.1.0.zip`.
2. Back up the skin's `xml/Includes_MediaMenu.xml`.
3. In the `<include name="PVRSideBar">` section, locate the horizontal quick-nav `<grouplist id="6056">`.
4. Immediately after the existing quick-nav item with control ID `105` (TV Search), add:

```xml
<control type="radiobutton" id="106">
  <width>92</width>
  <height>92</height>
  <align>center</align>
  <aligny>center</aligny>
  <font></font>
  <texturefocus colordiffuse="$VAR[SkinColorVar]">buttons/roundbutton-fo.png</texturefocus>
  <texturenofocus />
  <radioposx>26</radioposx>
  <radioposy>0</radioposy>
  <radiowidth>40</radiowidth>
  <radioheight>40</radioheight>
  <textureradioonfocus>icons/submenu/channels.png</textureradioonfocus>
  <textureradioonnofocus>icons/submenu/channels.png</textureradioonnofocus>
  <textureradioofffocus>icons/submenu/channels.png</textureradioofffocus>
  <textureradiooffnofocus>icons/submenu/channels.png</textureradiooffnofocus>
  <onclick>ActivateWindow(Videos,plugin://plugin.video.xtreamcodes.browser/,return)</onclick>
</control>
```

5. Restart Kodi or reload the skin.

The new icon opens a dedicated channel browser: groups are listed first, selecting one opens its channels, and Kodi's Back action returns to the group list. The first item in the browser is global channel search. This is a separate browser view, not a replacement of Kodi's native PVR window; the existing PVR window, logos, EPG settings and zap behavior remain untouched.

If the button does not appear, restore the backup and check that the block was inserted inside the `grouplist id="6056"`, not outside it.
