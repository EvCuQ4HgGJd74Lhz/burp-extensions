"""
GAP by /XNL-h4ck3r (@xnl_h4ck3r)

Respect and thanks go to @HolyBugx for help with the original versions ideas, testing and patience!
Also, thanks to so many people who have made suggestions, reported issues, and helped me test each version I release!

Get full instructions at https://github.com/xnl-h4ck3r/GAP-Burp-Extension/blob/main/GAP%20Help.md or press the Help button on the GAP tab

Good luck and good hunting! If you really love the tool (or any others), or they helped you find an awesome bounty, consider BUYING ME A COFFEE! (https://ko-fi.com/xnlh4ck3r) (I could use the caffeine!)
"""
VERSION="2.4"

from burp import IBurpExtender, IContextMenuFactory, IScopeChangeListener, ITab
from javax.swing import (
    JFrame,
    JMenuItem,
    GroupLayout,
    JPanel,
    JCheckBox,
    JTextField,
    JLabel,
    JButton,
    JScrollPane,
    JTextArea,
    ScrollPaneConstants,
    JFileChooser,
    BorderFactory,
    JEditorPane,
    ImageIcon,
    JProgressBar
)
from java.util import ArrayList
from urlparse import urlparse
from java.io import PrintWriter, File
from java.awt import Color, Font, Image, Cursor, Desktop
from java.awt.event import KeyListener
from java.net import URL, URI
from java.lang import System
from javax.imageio import ImageIO

import os
import platform
import re
import pickle
import threading
import time
WORDLIST_IMPORT_ERROR = ""
try:
    from bs4 import BeautifulSoup, Comment
except Exception as e:
    WORDLIST_IMPORT_ERROR = "The following error occurred when importing beauttifulsoup4: " + str(e) + "\nPlease make sure you have followed the installation instructions on https://github.com/xnl-h4ck3r/GAP-Burp-Extension#installation\n"
    print("WARNING: Could not import beauttifulsoup4 for word mode: " + str(e))
    
# Try to import html5lib as a parser for beautifulsoup4 because it's more accurate than the default html.parser
try:
    html5libInstalled = True
    import html5lib
except Exception as e:
    html5libInstalled = False
    
_debug = False

# Common parameter names often used across targets, mainly for redirects. These can be included in the collected parameter list by checking the "Include the list of common params in list" option
# NOTE: Some are the same, but different case in places as these can be treated differently
COMMON_PARAMS = [
    "page",
    "callback",
    "next",
    "prev",
    "previous",
    "ref",
    "go",
    "return",
    "goto",
    "r_url",
    "returnurl",
    "returnuri",
    "location",
    "locationurl",
    "return_url",
    "goTo",
    "r_Url",
    "r_URL",
    "returnUrl",
    "returnURL",
    "returnUri",
    "retunrURI",
    "locationUrl",
    "locationURL",
    "return_Url",
    "return_URL",
    "site",
    "debug",
    "active",
    "admin",
    "id",
    "cancelUrl",
    "cancelURL",
    "cancel_url",
    "forward",
    "rurl",
    "r_url",
    "out",
    "redirect",
    "view",
    "to",
    "url",
    "uri",
    "target",
    "dest",
    "destination",
    "redir",
    "redirecturl",
    "redirect_url",
    "redirecturi",
    "redirect_uri",
    "relaystate",
    "RelayState",
    "u",
    "n",
    "forward",
    "forwardurl",
    "forward_url",
    "src",
    "endpoint",
    "srcURL",
    "q",
    "link",
    "import_url",
    "images",
    "image",
    "id",
    "html",
    "ewsUrl",
    "downloadpath",
    "destination",
    "consumerUri",
    "add_imageurl"
]

# A comma separated list of Link exclusions used when no options have been saved, or when the "Restore defaults" button is pressed
# Links are NOT displayed if they contain these strings. This just applies to the links found in endpoints, not the origin link in which it was found
DEFAULT_EXCLUSIONS = ".css,.jpg,.jpeg,.png,.svg,.img,.gif,.mp4,.flv,.ogv,.webm,.webp,.mov,.mp3,.m4a,.m4p,.scss,.tif,.tiff,.ttf,.otf,.woff,.woff2,.bmp,.ico,.eot,.htc,.rtf,.swf,.image,w3.org,doubleclick.net,youtube.com,.vue,jquery,bootstrap,font,jsdelivr.net,vimeo.com,pinterest.com,facebook,linkedin,twitter,instagram,google,mozilla.org,jibe.com,schema.org,schemas.microsoft.com,wordpress.org,w.org,wix.com,parastorage.com,whatwg.org,polyfill.io,typekit.net,schemas.openxmlformats.org,openweathermap.org,openoffice.org,reactjs.org,angularjs.org,java.com,purl.org,/image,/img,/css,/wp-json,/wp-content,/wp-includes,/theme,/audio,/captcha,/font,robots.txt,node_modules,.wav,.gltf,.pict,.svgz,.eps,.midi,.mid,.avif"

# A comma separated list of Content-Type exclusions used to determine what requests are checked for potential links
# These content types will NOT be checked
CONTENTTYPE_EXCLUSIONS = "text/css,image/jpeg,image/jpg,image/png,image/svg+xml,image/gif,image/tiff,image/webp,image/bmp,image/x-icon,image/vnd.microsoft.icon,font/ttf,font/woff,font/woff2,font/x-woff2,font/x-woff,font/otf,audio/mpeg,audio/wav,audio/webm,audio/aac,audio/ogg,audio/wav,audio/webm,video/mp4,video/mpeg,video/webm,video/ogg,video/mp2t,video/webm,video/x-msvideo,application/font-woff,application/font-woff2,application/vnd.android.package-archive,binary/octet-stream,application/octet-stream,application/pdf,application/x-font-ttf,application/x-font-otf,application/x-font-woff,application/vnd.ms-fontobject,image/avif,application/zip,application/x-zip-compressed,application/x-msdownload,application/x-apple-diskimage,application/x-rpm,application/vnd.debian.binary-package"

# A comma separated list of file extension exclusions used when the content-type isn't available. Files with these extensions will NOT be checked
FILEEXT_EXCLUSIONS = ".zip,.dmg,.rpm,.deb,.gz,.tar,.jpg,.jpeg,.png,.svg,.img,.gif,.mp4,.flv,.ogv,.webm,.webp,.mov,.mp3,.m4a,.m4p,.scss,.tif,.tiff,.ttf,.otf,.woff,.woff2,.bmp,.ico,.eot,.htc,.rtf,.swf,.image,.wav,.gltf,.pict,.svgz,.eps,.midi,.mid"

# The default value (used until options are saved, or when the "Restore defaults" button is pressed) for the generated query string of all parameters.
DEFAULT_QSV = "XNLV"

# A list of files used in the Link Finding Regex. These are used in the 5th capturing group that aren't obvious links, but could be files
LINK_REGEX_FILES = "php|php3|php5|asp|aspx|ashx|cfm|cgi|pl|jsp|jspx|json|js|action|html|xhtml|htm|bak|do|txt|wsdl|wadl|xml|xls|xlsx|bin|conf|config|bz2|bzip2|gzip|tar\.gz|tgz|log|src|zip|js\.map"

# Default content types where to look for Words
DEFAULT_WORDS_CONTENT_TYPES = "text/html,application/xml,application/json,text/plain,application/xhtml+xml,application/ld+json,text/xml"

# Default english "stop word" list
DEFAULT_STOP_WORDS = "a,aboard,about,above,across,after,afterwards,again,against,all,almost,alone,along,already,also,although,always,am,amid,among,amongst,an,and,another,any,anyhow,anyone,anything,anyway,anywhere,are,around,as,at,back,be,became,because,become,becomes,becoming,been,before,beforehand,behind,being,below,beneath,beside,besides,between,beyond,both,bottom,but,by,can,cannot,cant,con,concerning,considering,could,couldnt,cry,de,describe,despite,do,done,down,due,during,each,eg,eight,either,eleven,else,elsewhere,empty,enough,etc,even,ever,every,everyone,everything,everywhere,except,few,fifteen,fifty,fill,find,fire,first,five,for,former,formerly,forty,found,four,from,full,further,get,give,go,had,has,hasnt,have,he,hence,her,here,hereafter,hereby,herein,hereupon,hers,herself,him,himself,his,how,however,hundred,i,ie,if,in,inc,indeed,inside,interest,into,is,it,its,itself,keep,last,latter,latterly,least,less,like,ltd,made,many,may,me,meanwhile,might,mill,mine,more,moreover,most,mostly,move,much,must,my,myself,name,namely,near,neither,never,nevertheless,next,nine,no,nobody,none,noone,nor,not,nothing,now,nowhere,of,off,often,on,once,one,only,onto,or,other,others,otherwise,our,ours,ourselves,out,outside,over,own,part,past,per,perhaps,please,put,rather,re,regarding,round,same,see,seem,seemed,seeming,seems,serious,several,she,should,show,side,since,sincere,six,sixty,so,some,somehow,someone,something,sometime,sometimes,somewhere,still,such,take,ten,than,that,the,their,them,themselves,then,thence,there,thereafter,thereby,therefore,therein,thereupon,these,they,thick,thin,third,this,those,though,three,through,throughout,thru,thus,to,together,too,top,toward,towards,twelve,twenty,two,un,under,underneath,until,unto,up,upon,us,very,via,want,was,we,well,went,were,weve,what,whatever,when,whence,whenever,where,whereafter,whereas,whereby,wherein,whereupon,wherever,whether,which,while,whilst,whither,whoever,whole,whom,whose,why,will,with,within,without,would,yet,you,youll,your,youre,yours,yourself,yourselves,youve"

# The GAP Help file and 404 message if unavailable
GAP_HELP_URL = "https://github.com/xnl-h4ck3r/GAP-Burp-Extension/blob/main/GAP%20Help.md"
GAP_HELP_URL_BUTTON = (
    "https://raw.githubusercontent.com/xnl-h4ck3r/GAP-Burp-Extension/main/GAP%20Help.md"
)
GAP_HELP_404 = (
    "<h1>Oops... mind the GAP!</h1><p>Sorry, this should be displaying the content of the following page:<p><a href="
    + GAP_HELP_URL
    + ">"
    + GAP_HELP_URL
    + "</a><p>However, there seems to be a problem connecting to that resource.<p>Please try again later. If the problem persists, please raise an issue on Github."
)

# URLs for icons used
HELP_ICON = (
    "https://cdn0.iconfinder.com/data/icons/simply-orange-1/128/questionssvg-512.png"
)
DIR_ICON = "https://cdn0.iconfinder.com/data/icons/simply-orange-1/128/currency_copysvg-512.png"

# Enumeration of request parameter types identified by Burp
PARAM_URL = 0
PARAM_BODY = 1
PARAM_COOKIE = 2
PARAM_XML = 3
PARAM_XML_ATTR = 4
PARAM_MULTIPART_ATTR = 5
PARAM_JSON = 6

# The default maximum length of words to add
DEFAULT_MAX_WORD_LEN = "40"

# The default value for Link Prefix
DEFAULT_LINK_PREFIX = "https://www.CHANGE.THIS"

# Get the GAP logo from the Github page
URL_GAP_LOGO = "https://github.com/xnl-h4ck3r/GAP-Burp-Extension/raw/main/GAP/images/banner.png"

# KoFi links for buying me a coffee
URL_KOFI = "https://ko-fi.com/B0B3CZKR5"
URL_KOFI_BUTTON = "https://storage.ko-fi.com/cdn/kofi2.png?v=3"

# My Github URL
URL_GITHUB = "https://github.com/xnl-h4ck3r"

class BurpExtender(IBurpExtender, IContextMenuFactory, ITab):
    def registerExtenderCallbacks(self, callbacks):
        """
        Registers the extension and initializes
        """
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._stderr = PrintWriter(callbacks.getStderr(), True)
        self.context = None
        self.roots = set()
        self.param_list = set()
        self.link_list = set()
        self.linkUrl_list = set()
        self.word_list = set()
        self.lstStopWords = {}
        callbacks.setExtensionName("GAP")
        callbacks.registerContextMenuFactory(self)
        callbacks.registerScopeChangeListener(self.scopeChanged)
        self.dictResponseUrls = {}
        self.dictCheckedLinks = {}
        self.flagCANCEL = False

        # Take the LINK_REGEX_FILES values and build a string of any values over 4 characters or has a number in it
        # This is used in the 4th capturing group Link Finding regex
        lstFileExt = LINK_REGEX_FILES.split("|")
        self.LINK_REGEX_NONSTANDARD_FILES = ""
        for ext in lstFileExt:
            if len(ext) > 4 or any(chr.isdigit() for chr in ext):
                if self.LINK_REGEX_NONSTANDARD_FILES == "":
                    self.LINK_REGEX_NONSTANDARD_FILES = ext
                else:
                    self.LINK_REGEX_NONSTANDARD_FILES = (
                        self.LINK_REGEX_NONSTANDARD_FILES + "|" + ext
                    )

        # Compile the link regex
        self.REGEX_LINKS = re.compile(r"(?:^|\"|'|\\n|\\r|\n|\r|\s)(((?:[a-zA-Z]{1,10}:\/\/|\/\/)([^\"'\/]{1,}\.[a-zA-Z]{2,}|localhost)[^\"'\n\s]{0,})|((?:\/|\.\.\/|\.\/)[^\"'><,;| *()(%%$^\/\\\[\]][^\"'><,;|()\s]{1,})|([a-zA-Z0-9_\-\/]{1,}\/[a-zA-Z0-9_\-\/]{1,}\.(?:[a-zA-Z]{1,4}" + self.LINK_REGEX_NONSTANDARD_FILES + ")(?:[\?|\/][^\"|']{0,}|))|([a-zA-Z0-9_\-]{1,}\.(?:" + LINK_REGEX_FILES + ")(?:\?[^\"|^']{0,}|)))(?:\"|'|\\n|\\r|\n|\r|\s|$)|(?<=^Disallow:\s)[^\$\n]*|(?<=^Allow:\s)[^\$\n]*|(?<= Domain\=)[^\";']*|(?<=\<)https?:\/\/[^>\n]*|(?<=\=)\s*\/[0-9a-zA-Z]+[^>\n]*", re.IGNORECASE)
        
        # Regex for checking Burp url when checking if in scope
        self.REGEX_BURPURL = re.compile(r"^(https?:)?\/\/([-a-zA-Z0-9_]+\.)?[-a-zA-Z0-9_]+\.[-a-zA-Z0-9_\.\?\#\&\=]+$", re.IGNORECASE)
        
        # Regex for checking content-type
        self.REGEX_CONTENTTYPE = re.compile(r"(?<=Content-Type\:\s)[a-zA-Z\-].+\/[a-zA-Z\-].+?(?=\s|\;)", re.IGNORECASE)
        
        # Make the Stop Word list and make all lower case
        try:
            self.lstStopWords = DEFAULT_STOP_WORDS.split(",")
            self.lstStopWords = list(map(str.lower,self.lstStopWords))
        except Exception as e:
            self._stderr.println("registerExtenderCallbacks 1")
            self._stderr.println(e)

                
        # Create the UI part of GAP
        self._createUI()

        # Display welcome message
        print("GAP - Version " + VERSION)
        print("by @xnl_h4ck3r\n")
        print(
            "The full Help documentation can be found at "
            + GAP_HELP_URL
            + " or from the Help icon on the GAP tab\n"
        )
        if _debug:
            print("DEBUG MODE ON\n")
        
        print("If you ever see anything in the Errors tab, please raise an issue on Github so I can fix it!")
        print("Want to buy me a coffee?! - " + URL_KOFI + "\n")
        
        try:
            if not html5libInstalled:
                print("WARNING: Could not import html5lib for more accurate parsing of words by beatifulsoup4 library.")
        except:
            pass
        
    def _createUI(self):
        """
        Creates the Java Swing UI for GAP
        """
        # Derive the default font and size
        test = JLabel()
        FONT_FAMILY = test.getFont().getFamily()
        FONT_SIZE = test.getFont().getSize()

        # Create a font for headers and other non standard stuff
        FONT_HEADER = Font(FONT_FAMILY, Font.BOLD, FONT_SIZE + 2)
        FONT_HELP = Font(FONT_FAMILY, Font.BOLD, FONT_SIZE)
        FONT_GAP_MODE = Font(FONT_FAMILY, Font.BOLD, FONT_SIZE)
        FONT_LINK_OPTIONS = Font(FONT_FAMILY, Font.BOLD, FONT_SIZE - 2)

        # Set the colour for Burp Orange
        COLOR_BURP_ORANGE = Color(0xE36B1E)
        # Set colour for warning messages
        COLOR_WARNING = Color(0xE3251E)
        
        # Links section
        self.lblLinkOptions = JLabel("Links mode options:")
        self.lblLinkOptions.setFont(FONT_HEADER)
        self.lblLinkOptions.setForeground(COLOR_BURP_ORANGE)
        
        # Parameter sections
        self.lblWhichParams = JLabel("Parameters mode options:")
        self.lblWhichParams.setFont(FONT_HEADER)
        self.lblWhichParams.setForeground(COLOR_BURP_ORANGE)

        # Request parameter section
        self.lblRequestParams = JLabel("REQUEST PARAMETERS")
        fnt = self.lblRequestParams.getFont()
        self.lblRequestParams.setFont(fnt.deriveFont(fnt.getStyle() | Font.BOLD))
        self.cbParamUrl = self.defineCheckBox("Query string params")
        self.cbParamBody = self.defineCheckBox("Message body params")
        self.cbParamMultiPart = self.defineCheckBox(
            "Param attribute in multi-part message body"
        )
        self.cbParamJson = self.defineCheckBox("JSON params")
        self.cbParamCookie = self.defineCheckBox("Cookie names", False)
        self.cbParamXml = self.defineCheckBox(
            "Items of data in XML structure", False
        )
        self.cbParamXmlAttr = self.defineCheckBox(
            "Value of tag attributes in XML structure", False
        )

        # Response parameter section
        self.lblResponseParams = JLabel("RESPONSE PARAMETERS")
        fnt = self.lblResponseParams.getFont()
        self.lblResponseParams.setFont(fnt.deriveFont(fnt.getStyle() | Font.BOLD))
        self.cbParamJSONResponse = self.defineCheckBox("JSON params", False)
        self.cbParamXMLResponse = self.defineCheckBox(
            "Value of tag attributes in XML structure", False
        )
        self.cbParamInputField = self.defineCheckBox(
            "Name and Id attributes of HTML input fields", False
        )
        self.cbParamJSVars = self.defineCheckBox(
            "Javascript variables and constants", False
        )
        self.cbParamMetaName = self.defineCheckBox("Name attribute of Meta tags", False)
        self.cbParamFromLinks = self.defineCheckBox("Params from links found", False)
        self.cbParamsEnabled = self.defineCheckBox("Parameters", True)
        self.cbParamsEnabled.addItemListener(self.cbParamsEnabled_clicked)
        self.cbLinksEnabled = self.defineCheckBox("Links", True)
        self.cbLinksEnabled.addItemListener(self.cbLinksEnabled_clicked)
        self.cbWordsEnabled = self.defineCheckBox("Words", True)
        self.cbWordsEnabled.addItemListener(self.cbWordsEnabled_clicked)

        # GAP Mode group
        self.lblMode = JLabel("GAP Mode: ")
        self.lblMode.setFont(FONT_GAP_MODE)
        self.lblMode.setForeground(COLOR_BURP_ORANGE)
        self.grpMode = JPanel()
        self.grpMode.setBorder(
            BorderFactory.createLineBorder(COLOR_BURP_ORANGE, 2, True)
        )
        self.grpMode.add(self.lblMode)
        self.grpMode.add(self.cbParamsEnabled)
        self.grpMode.add(self.cbLinksEnabled)
        self.grpMode.add(self.cbWordsEnabled)

        # Words sections
        self.lblWhichWords = JLabel("Words mode options:")
        self.lblWhichWords.setFont(FONT_HEADER)
        self.lblWhichWords.setForeground(COLOR_BURP_ORANGE)

        # Request words section
        self.cbWordPlurals = self.defineCheckBox("Create singular/plural words")
        self.cbWordPaths = self.defineCheckBox("Include URL path words?")
        self.cbWordParams = self.defineCheckBox("Include potential params?")
        self.cbWordComments = self.defineCheckBox("Include HTML comments?")
        self.cbWordImgAlt = self.defineCheckBox("Include IMG ALT attribute?")
        self.cbWordDigits = self.defineCheckBox("Include words with digits?")
        self.lblWordsMaxLen = JLabel("Maximum length of words")
        self.lblWordsMaxLen2 = JLabel("(min. 3 - excludes plurals)")
        self.inWordsMaxlen = JTextField("", 2 ,actionPerformed=self.checkMaxWordsLen)

        # Set the Help button as an icon
        # NOTE: This has been commented out because I could not get it to display correctly at different font size settings
        """ 
        imageUrl = URL(HELP_ICON)         
        img = ImageIO.read(imageUrl)
        resizedImg = img.getScaledInstance(37, 37, Image.SCALE_DEFAULT)       
        imgIcon = ImageIcon(resizedImg)
        self.btnHelp = JButton(imgIcon, actionPerformed=self.btnHelp_clicked)
        self.btnHelp.setContentAreaFilled(False)
        self.btnHelp.setBorderPainted(False)
        """
        # If can't set as an icon, set as a normal button
        self.lblHelp = JLabel("Click for help -->")
        self.lblHelp.setFont(FONT_GAP_MODE)
        self.lblHelp.setForeground(COLOR_BURP_ORANGE)
        self.btnHelp = JButton("?", actionPerformed=self.btnHelp_clicked)
        self.btnHelp.setFont(FONT_HELP)
        self.btnHelp.setForeground(Color.WHITE)
        self.btnHelp.setBorder(
            BorderFactory.createLineBorder(COLOR_BURP_ORANGE, 2, True)
        )
        self.btnHelp.setContentAreaFilled(True)
        self.btnHelp.setBackground(COLOR_BURP_ORANGE)
        self.btnHelp.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))
        self.grpHelp = JPanel()
        self.grpHelp.setBorder(
            BorderFactory.createLineBorder(COLOR_BURP_ORANGE, 2, True)
        )
        self.grpHelp.add(self.lblHelp)
        self.grpHelp.add(self.btnHelp)
        self.btnHelp.setToolTipText("Click me for help!")
        
        # Set KoFi button
        try:
            initialImg = ImageIO.read(URL(URL_KOFI_BUTTON))
            width = int(round(self.grpHelp.getPreferredSize().width * 0.8))
            height = int(round(self.grpHelp.getPreferredSize().height * 0.85))
            scaledImg = initialImg.getScaledInstance(width, height, Image.SCALE_SMOOTH)
            self.grpKoFi = JButton(ImageIcon(scaledImg),actionPerformed=self.btnKoFi_clicked)
            self.grpKoFi.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))
            self.grpKoFi.setToolTipText("Buy Me a Coffee!")
            self.grpKoFi.setBorderPainted(False)
            self.grpKoFi.setContentAreaFilled(False)
        except:
            self.btnKoFi = JButton("Buy Me a Coffee!",actionPerformed=self.btnKoFi_clicked)
            self.btnKoFi.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))
            self.btnKoFi.setFont(FONT_HELP)
            self.btnKoFi.setForeground(Color.WHITE)
            self.btnKoFi.setBorder(
                BorderFactory.createLineBorder(COLOR_BURP_ORANGE, 2, True)
            )
            self.btnKoFi.setContentAreaFilled(True)
            self.btnKoFi.setBackground(COLOR_BURP_ORANGE)
            self.grpKoFi = JPanel()
            self.grpKoFi.setBorder(
                BorderFactory.createLineBorder(COLOR_BURP_ORANGE, 2, True)
            )
            self.grpKoFi.add(self.btnKoFi)

        # Set the GAP logo
        try:
            initialImg = ImageIO.read(URL(URL_GAP_LOGO))
            width = self.grpMode.getPreferredSize().width+self.grpHelp.getPreferredSize().width+self.grpKoFi.getPreferredSize().width
            height = int(round(width / 15))
            scaledImg = initialImg.getScaledInstance(width, height, Image.SCALE_SMOOTH)
            self.btnLogo = JButton(ImageIcon(scaledImg),actionPerformed=self.btnLogo_clicked)
            self.btnLogo.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))
            self.btnLogo.setToolTipText("Check out my Github page")
        except:
            self.btnLogo = JButton()
            self.btnLogo.setVisible(False)
            
        # Output options section
        self.lblOutputOptions = JLabel("Other options:")
        self.lblOutputOptions.setFont(FONT_HEADER)
        self.lblOutputOptions.setForeground(COLOR_BURP_ORANGE)
        self.cbIncludeCommonParams = self.defineCheckBox(
            "Include common parameters?", True
        )
        self.cbIncludePathWords = self.defineCheckBox(
            "Include URL path words?", False
        )
        self.cbSiteMapEndpoints = self.defineCheckBox(
            "Include site map endpoints in link list?", False
        )
        self.cbLinkPrefix = self.defineCheckBox("Link prefix:")
        self.cbLinkPrefix.addItemListener(self.cbLinkPrefix_clicked)
        self.inLinkPrefix = JTextField(30,actionPerformed=self.checkLinkPrefix)
        self.cbUnPrefixed = self.defineCheckBox("Also include un-prefixed links?")
        self.lblPrefixWarning = JLabel("Warning: Invalid prefix")
        self.lblPrefixWarning.setVisible(False)
        self.lblPrefixWarning.setForeground(COLOR_WARNING)
        self.cbSaveFile = self.defineCheckBox("Auto save output to directory")
        self.cbSaveFile.addItemListener(self.cbSaveFile_clicked)
        self.inSaveDir = JTextField(30)
        self.inSaveDir.setEditable(False)
        self.btnChooseDir = JButton(
            "Choose...", actionPerformed=self.btnChooseDir_clicked
        )
        self.cbShowQueryString = self.defineCheckBox(
            "Show params as query string with value", False
        )
        self.cbShowQueryString.addItemListener(self.cbShowQueryString_clicked)
        self.lblQueryStringVal = JLabel("Concatenated param value")
        self.inQueryStringVal = JTextField(6)
        
        # The Restore/Save section
        self.btnSave = JButton("Save options", actionPerformed=self.btnSave_clicked)
        self.btnRestoreDefaults = JButton(
            "Restore defaults", actionPerformed=self.btnRestoreDefaults_clicked
        )
        self.btnCancel = JButton(
            "   COMPLETED    ", actionPerformed=self.btnCancel_clicked
        )
        self.btnCancel.setBackground(COLOR_BURP_ORANGE)
        self.btnCancel.setForeground(Color.WHITE)
        self.btnCancel.setFont(self.btnCancel.getFont().deriveFont(Font.BOLD))
        self.btnCancel.setVisible(False)
        # Create progress bar
        self.progBar = JProgressBar()
        self.progBar.setValue(0)
        self.progBar.setStringPainted(True)
        self.progBar.setVisible(False)
        self.progStage = JLabel()
        self.progStage.setVisible(False)
        self.progStage.setFont(FONT_HEADER)
        self.progStage.setForeground(COLOR_BURP_ORANGE)
        
        self.grpConfig = JPanel()
        self.grpConfig.add(self.btnRestoreDefaults)
        self.grpConfig.add(self.btnSave)
        self.grpConfig.add(JLabel("     "))
        self.grpConfig.add(self.btnCancel)
        self.grpConfig.add(self.progBar)
        self.grpConfig.add(self.progStage)

        # Potential parameters found section
        self.lblParamList = JLabel("Potential parameters found:")
        self.lblParamList.setFont(FONT_HEADER)
        self.lblParamList.setForeground(COLOR_BURP_ORANGE)
        self.outParamList = JTextArea(30, 100)
        self.outParamList.setLineWrap(False)
        self.outParamList.setEditable(False)
        self.scroll_outParamList = JScrollPane(self.outParamList)
        self.scroll_outParamList.setVerticalScrollBarPolicy(
            ScrollPaneConstants.VERTICAL_SCROLLBAR_AS_NEEDED
        )
        self.scroll_outParamList.setHorizontalScrollBarPolicy(
            ScrollPaneConstants.HORIZONTAL_SCROLLBAR_AS_NEEDED
        )
        self.outParamQuery = JTextArea(30, 100)
        self.outParamQuery.setLineWrap(True)
        self.outParamQuery.setEditable(False)
        
        # Potential links found section
        self.lblLinkList = JLabel("Potential links found:")
        self.lblLinkList.setFont(FONT_HEADER)
        self.lblLinkList.setForeground(COLOR_BURP_ORANGE)
        self.outLinkList = JTextArea(30, 100)
        self.outLinkList.setLineWrap(False)
        self.outLinkList.setEditable(False)
        self.scroll_outLinkList = JScrollPane(self.outLinkList)
        self.scroll_outLinkList.setVerticalScrollBarPolicy(
            ScrollPaneConstants.VERTICAL_SCROLLBAR_AS_NEEDED
        )
        self.scroll_outLinkList.setHorizontalScrollBarPolicy(
            ScrollPaneConstants.HORIZONTAL_SCROLLBAR_AS_NEEDED
        )
        self.cbShowLinkOrigin = self.defineCheckBox("Show origin endpoint", False)
        self.cbShowLinkOrigin.setFont(FONT_LINK_OPTIONS)
        self.cbShowLinkOrigin.setVisible(False)
        self.cbShowLinkOrigin.addItemListener(self.changeLinkDisplay)
        self.cbInScopeOnly = self.defineCheckBox("In scope only", False)
        self.cbInScopeOnly.setFont(FONT_LINK_OPTIONS)
        self.cbInScopeOnly.setVisible(False)
        self.cbInScopeOnly.addItemListener(self.changeLinkDisplay)
        self.lblLinkFilter = JLabel("Link filter:")
        self.lblLinkFilter.setEnabled(False)
        self.btnFilter = JButton("Apply filter", actionPerformed=self.btnFilter_clicked)
        self.btnFilter.setEnabled(False)
        self.cbLinkFilterNeg = self.defineCheckBox("Negative match", False)
        self.cbLinkFilterNeg.setEnabled(False)
        self.cbLinkCaseSens = self.defineCheckBox("Case sensitive", False)
        self.cbLinkCaseSens.setEnabled(False)
        self.inLinkFilter = JTextField(10)
        self.keyListen = CustomKeyListener(self.btnFilter)
        self.inLinkFilter.addKeyListener(self.keyListen)
        self.inLinkFilter.setEnabled(False)
        self.grpLinkFilter = JPanel()
        self.grpLinkFilter.add(self.lblLinkFilter)
        self.grpLinkFilter.add(self.inLinkFilter)
        self.grpLinkFilter.add(self.cbLinkFilterNeg)
        self.grpLinkFilter.add(self.cbLinkCaseSens)
        self.grpLinkFilter.add(self.btnFilter)
        
        # Potential words found section
        if WORDLIST_IMPORT_ERROR != "":
            self.lblWordList = JLabel("Words found - UNAVAILABLE:")
        else:
            self.lblWordList = JLabel("Words found:")
        self.lblWordList.setFont(FONT_HEADER)
        self.lblWordList.setForeground(COLOR_BURP_ORANGE)
        self.outWordList = JTextArea(30, 100)
        self.outWordList.setLineWrap(False)
        self.outWordList.setEditable(False)
        if WORDLIST_IMPORT_ERROR != "":
            self.outWordList.text = WORDLIST_IMPORT_ERROR
        self.scroll_outWordList = JScrollPane(self.outWordList)
        self.scroll_outWordList.setVerticalScrollBarPolicy(
            ScrollPaneConstants.VERTICAL_SCROLLBAR_AS_NEEDED
        )
        self.scroll_outWordList.setHorizontalScrollBarPolicy(
            ScrollPaneConstants.HORIZONTAL_SCROLLBAR_AS_NEEDED
        )
        self.lblStopWords = JLabel("Stop words:")
        self.inStopWords = JTextField(30)
        
        # Initialise text fields to hold variations of outLinkList JTextArea
        self.txtLinksWithURL = ""
        self.txtLinksOnly = ""
        self.txtLinksWithURLInScopeOnly = ""
        self.txtLinksOnlyInScopeOnly = ""
        self.txtLinksFiltered = ""

        # Definition of config tab
        self.tab = JPanel()
        layout = GroupLayout(self.tab)
        self.tab.setLayout(layout)
        layout.setAutoCreateGaps(True)
        layout.setAutoCreateContainerGaps(True)

        # Set up a field for comma separated exclusion strings
        self.lblExclusions = JLabel(" Link exclusions:")
        self.inExclusions = JTextField(300)

        # Restore saved config settings
        self.restoreSavedConfig()

        # Set UI layout
        layout.setHorizontalGroup(
            layout.createParallelGroup()
            .addGroup(
                layout.createSequentialGroup()
                .addGroup(
                    layout.createParallelGroup()
                    .addComponent(self.btnLogo,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                )
                    .addGroup(
                        layout.createSequentialGroup()
                        .addComponent(
                            self.grpMode,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                        .addComponent(
                            self.grpHelp,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                        .addComponent(self.grpKoFi,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,)
                    )
                    .addComponent(self.lblWhichParams)
                    .addGroup(
                        layout.createSequentialGroup()
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.cbIncludePathWords)
                            .addComponent(self.lblRequestParams)
                            .addComponent(self.cbParamUrl)
                            .addComponent(self.cbParamBody)
                            .addComponent(self.cbParamMultiPart)
                            .addComponent(self.cbParamJson)
                            .addComponent(self.cbParamCookie)
                            .addComponent(self.cbParamXml)
                            .addComponent(self.cbParamXmlAttr)
                        )
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.cbIncludeCommonParams)
                            .addComponent(self.lblResponseParams)
                            .addComponent(self.cbParamJSONResponse)
                            .addComponent(self.cbParamXMLResponse)
                            .addComponent(self.cbParamInputField)
                            .addComponent(self.cbParamJSVars)
                            .addComponent(self.cbParamMetaName)
                            .addComponent(self.cbParamFromLinks)
                        )
                    )
                    .addComponent(self.lblLinkOptions)
                    .addGroup(
                        layout.createSequentialGroup()
                        .addComponent(self.cbLinkPrefix)
                        .addComponent(self.inLinkPrefix)
                        .addComponent(self.lblPrefixWarning)
                    )
                    .addGroup(
                        layout.createSequentialGroup()
                        .addComponent(self.cbUnPrefixed)
                        .addComponent(self.cbSiteMapEndpoints)
                    )
                    .addComponent(self.lblWhichWords)
                    .addGroup(
                        layout.createSequentialGroup()
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.cbWordDigits)
                            .addComponent(self.cbWordPlurals)
                            .addGroup(
                                layout.createSequentialGroup()
                                .addComponent(self.lblWordsMaxLen)
                                .addComponent(
                                    self.inWordsMaxlen,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                )
                            )       
                        )
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.cbWordComments)
                            .addComponent(self.cbWordImgAlt)
                            .addComponent(self.lblWordsMaxLen2)
                        )
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.cbWordPaths)
                            .addComponent(self.cbWordParams)
                        )
                    )
                    .addComponent(self.lblOutputOptions)
                    .addGroup(
                        layout.createSequentialGroup()
                        .addComponent(self.cbSaveFile)
                        .addComponent(self.inSaveDir)
                        .addComponent(self.btnChooseDir)
                    )
                    .addComponent(
                        self.grpConfig,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                )
                .addGroup(
                    layout.createParallelGroup()
                    .addGroup(
                        layout.createSequentialGroup()
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.lblParamList)
                            .addComponent(self.scroll_outParamList)
                            .addGroup(
                                layout.createSequentialGroup()
                                .addComponent(self.cbShowQueryString)
                                .addComponent(
                                    self.inQueryStringVal,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                )
                            )
                        )
                        .addGroup(
                            layout.createParallelGroup()
                            .addComponent(self.lblWordList)
                            .addComponent(self.scroll_outWordList)
                            .addGroup(
                                layout.createSequentialGroup()
                                .addComponent(self.lblStopWords)
                                .addComponent(self.inStopWords)
                            )
                        )
                    )
                    .addGroup(
                        layout.createSequentialGroup()
                        .addComponent(self.lblLinkList)
                        .addComponent(self.cbShowLinkOrigin)
                        .addComponent(self.cbInScopeOnly)
                    )
                    .addComponent(self.scroll_outLinkList)
                    .addComponent(
                        self.grpLinkFilter,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addGroup(
                        layout.createSequentialGroup()
                        .addComponent(self.lblExclusions)
                        .addComponent(
                            self.inExclusions,
                            GroupLayout.DEFAULT_SIZE,
                            GroupLayout.DEFAULT_SIZE,
                            GroupLayout.DEFAULT_SIZE,
                        )
                    )
                )
            )
        )

        layout.setVerticalGroup(
            layout.createSequentialGroup()
            .addGroup(
                layout.createParallelGroup()
                .addGroup(
                    layout.createSequentialGroup()
                    .addComponent(self.btnLogo,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                )
                    .addGroup(
                            layout.createParallelGroup()
                            .addComponent(
                                self.grpMode,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                            )
                            .addComponent(
                                self.grpHelp,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                            )
                            .addComponent(self.grpKoFi,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,
                                GroupLayout.PREFERRED_SIZE,)
                        )
                    .addComponent(self.lblWhichParams)
                    .addGroup(
                        layout.createParallelGroup()
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.cbIncludePathWords)
                            .addComponent(self.lblRequestParams)
                            .addComponent(self.cbParamUrl)
                            .addComponent(self.cbParamBody)
                            .addComponent(self.cbParamMultiPart)
                            .addComponent(self.cbParamJson)
                            .addComponent(self.cbParamCookie)
                            .addComponent(self.cbParamXml)
                            .addComponent(self.cbParamXmlAttr)
                        )
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.cbIncludeCommonParams)
                            .addComponent(self.lblResponseParams)
                            .addComponent(self.cbParamJSONResponse)
                            .addComponent(self.cbParamXMLResponse)
                            .addComponent(self.cbParamInputField)
                            .addComponent(self.cbParamJSVars)
                            .addComponent(self.cbParamMetaName)
                            .addComponent(self.cbParamFromLinks)
                        )
                    )
                    .addComponent(self.lblLinkOptions)
                    .addGroup(
                        layout.createParallelGroup()
                        .addComponent(self.cbLinkPrefix)
                        .addComponent(self.inLinkPrefix,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,)
                        .addComponent(self.lblPrefixWarning)
                    )
                    .addGroup(
                        layout.createParallelGroup()
                        .addComponent(self.cbUnPrefixed)
                        .addComponent(self.cbSiteMapEndpoints)
                    )
                    .addComponent(self.lblWhichWords)
                    .addGroup(
                        layout.createParallelGroup()
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.cbWordDigits)
                            .addComponent(self.cbWordPlurals)
                            .addGroup(
                                layout.createParallelGroup()
                                .addComponent(self.lblWordsMaxLen)
                                .addComponent(
                                    self.inWordsMaxlen,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                )
                            )
                        )
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.cbWordComments)
                            .addComponent(self.cbWordImgAlt)
                            .addComponent(self.lblWordsMaxLen2)
                        )
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.cbWordPaths)
                            .addComponent(self.cbWordParams)
                        )
                    )
                    .addComponent(self.lblOutputOptions)
                    .addGroup(
                        layout.createParallelGroup()
                        .addComponent(self.cbSaveFile)
                        .addComponent(
                            self.inSaveDir,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                        .addComponent(self.btnChooseDir)
                    )
                    .addComponent(
                        self.grpConfig,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                )
                .addGroup(
                    layout.createSequentialGroup()
                    .addGroup(
                        layout.createParallelGroup()
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.lblParamList)
                            .addComponent(
                                self.scroll_outParamList,
                                GroupLayout.DEFAULT_SIZE,
                                GroupLayout.DEFAULT_SIZE,
                                GroupLayout.DEFAULT_SIZE,
                            )
                            .addGroup(
                                layout.createParallelGroup()
                                .addComponent(self.cbShowQueryString)
                                .addComponent(
                                    self.inQueryStringVal,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                )
                            )
                        )
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.lblWordList)
                            .addComponent(
                                self.scroll_outWordList,
                                GroupLayout.DEFAULT_SIZE,
                                GroupLayout.DEFAULT_SIZE,
                                GroupLayout.DEFAULT_SIZE,
                            )
                            .addGroup(
                                layout.createParallelGroup()
                                .addComponent(self.lblStopWords)
                                .addComponent(self.inStopWords,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,
                                    GroupLayout.PREFERRED_SIZE,)
                            )
                        )
                    )
                    .addGroup(
                        layout.createParallelGroup()
                        .addComponent(self.lblLinkList)
                        .addComponent(self.cbShowLinkOrigin)
                        .addComponent(self.cbInScopeOnly)
                    )
                    .addComponent(
                        self.scroll_outLinkList,
                        GroupLayout.DEFAULT_SIZE,
                        GroupLayout.DEFAULT_SIZE,
                        GroupLayout.DEFAULT_SIZE,
                    )
                    .addComponent(
                        self.grpLinkFilter,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addGroup(
                        layout.createParallelGroup()
                        .addComponent(self.lblExclusions)
                        .addComponent(
                            self.inExclusions,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                    )
                )
            )
        )

        self._callbacks.addSuiteTab(self)
   
    def btnLogo_clicked(self, e=None):
        """
        The event called when the Logo image is clicked. Open a browser tab to Github page
        """
        try:
            Desktop.getDesktop().browse(URI(URL_GITHUB))
        except:
            pass
    
    def btnKoFi_clicked(self, e=None):
        """
        The event called when the KoFi button is clicked. Open a browser tab to KoFi page
        """
        try:
            Desktop.getDesktop().browse(URI(URL_KOFI))
        except:
            pass
        
    def cbParamsEnabled_clicked(self, e=None):
        """
        The event called when the "Parameters" check box is clicked
        """
        if self.cbParamsEnabled.isSelected():
            self.setEnabledParamOptions(True)
            self.lblParamList.visible = True
            if self.cbShowQueryString.isSelected():
                self.scroll_outParamList.setViewportView(self.outParamQuery)
            else:
                self.scroll_outParamList.setViewportView(self.outParamList)
            self.scroll_outParamList.visible = True
            self.cbShowQueryString.visible = True
            self.inQueryStringVal.visible = True
            # Also remove the word option "Include potential parameters"
            self.cbWordParams.visible = True
        else:
            self.setEnabledParamOptions(False)
            self.lblParamList.visible = False
            self.scroll_outParamList.visible = False
            self.cbShowQueryString.visible = False
            self.inQueryStringVal.visible = False
            # If no other mode is selected, reselect Links
            if not self.cbLinksEnabled.isSelected() and not self.cbWordsEnabled.isSelected():
                self.cbLinksEnabled.setSelected(True)
            # Also show the word option "Include potential parameters"
            self.cbWordParams.visible = False
            
    def cbLinksEnabled_clicked(self, e=None):
        """
        The event called when the "Links" check box is clicked
        """
        if self.cbLinksEnabled.isSelected():
            self.setEnabledLinkOptions(True)
            self.lblLinkList.visible = True
            self.cbInScopeOnly.visible = True
            self.cbShowLinkOrigin.visible = True
            self.scroll_outLinkList.visible = True
            self.grpLinkFilter.visible = True
            self.lblExclusions.visible = True
            self.inExclusions.visible = True
        else:
            self.setEnabledLinkOptions(False)
            self.lblLinkList.visible = False
            self.cbInScopeOnly.visible = False
            self.cbShowLinkOrigin.visible = False
            self.scroll_outLinkList.visible = False
            self.grpLinkFilter.visible = False
            self.lblExclusions.visible = False
            self.inExclusions.visible = False
            # If no other mode is selected, reselect Params
            if not self.cbParamsEnabled.isSelected() and not self.cbWordsEnabled.isSelected():
                self.cbParamsEnabled.setSelected(True)
            
    def cbWordsEnabled_clicked(self, e=None):
        """
        The event called when the "Words" check box is clicked
        """
        if self.cbWordsEnabled.isSelected():
            self.setEnabledWordOptions(True)
            self.lblWordList.visible = True
            self.scroll_outWordList.visible = True
            self.lblStopWords.visible = True
            self.inStopWords.visible = True
            if WORDLIST_IMPORT_ERROR != "":
                self.lblWordList.text = "Words found - UNAVAILABLE:"
        else:
            self.setEnabledWordOptions(False)
            self.lblWordList.visible = False
            self.scroll_outWordList.visible = False
            self.lblStopWords.visible = False
            self.inStopWords.visible = False
            # If no other mode is selected, reselect Links
            if not self.cbParamsEnabled.isSelected() and not self.cbLinksEnabled.isSelected():
                self.cbLinksEnabled.setSelected(True)
                
    def getTabCaption(self):
        return "GAP"

    def getUiComponent(self):
        return self.tab

    def scopeChanged(self, e=None):
        """
        The event called when the scope has changed in Burp
        """
        # If the scope has change then clear the dictionary that contains links in scope
        self.dictCheckedLinks.clear()

    def defineCheckBox(self, caption, selected=True, enabled=True):
        """
        Used when creating check box controls
        """
        checkBox = JCheckBox(caption)
        checkBox.setSelected(selected)
        checkBox.setEnabled(enabled)
        return checkBox

    def cbLinkPrefix_clicked(self, e=None):
        """
        The event called when the "Link prefix" checkbox is changed
        """
        # Only enable the Link Prefix field and Un_Prefixed checkbox if the Link Prefix checkbox is selected
        if self.cbLinkPrefix.isSelected():
            self.inLinkPrefix.setEnabled(True)
            self.cbUnPrefixed.setEnabled(True)
        else:
            self.inLinkPrefix.setEnabled(False)
            self.cbUnPrefixed.setEnabled(False)
            
    def cbSaveFile_clicked(self, e=None):
        """
        The event called when the "Auto save output directory" checkbox is changed
        """
        # Only enable the Save Directory field if the Save checkbox is selected
        if self.cbSaveFile.isSelected():
            self.inSaveDir.setEnabled(True)
        else:
            self.inSaveDir.setEnabled(False)

    def changeLinkDisplay(self, e=None):
        """
        The event called when the "Show origin endpoint" checkbox is changed
        """
        # Only show the origin URLs if the Show origin endpoint checkbox is ticked
        # The list of links depends on the settings selected
        if self.cbShowLinkOrigin.isSelected():
            if self.cbInScopeOnly.isSelected():
                self.outLinkList.text = self.txtLinksWithURLInScopeOnly
            else:
                self.outLinkList.text = self.txtLinksWithURL
        else:
            if self.cbInScopeOnly.isSelected():
                self.outLinkList.text = self.txtLinksOnlyInScopeOnly
            else:
                self.outLinkList.text = self.txtLinksOnly

        # Change the number of links in the "Potential links found" label depending if a filter is in place
        if str(self.countLinkUnique) == str(self.outLinkList.text.count("\n")):
            self.lblLinkList.text = (
                "Potential links found - " + str(self.countLinkUnique) + " unique:"
            )
        else:
            self.lblLinkList.text = (
                "Potential links found - "
                + str(self.outLinkList.text.count("\n"))
                + " filtered:"
            )

        # If there is a filter in place, apply it again
        if self.btnFilter.text == "Clear filter":
            self.btnFilter_clicked()

        # Reposition the display of the Link list to the start
        self.outLinkList.setCaretPosition(0)

    def cbShowQueryString_clicked(self, e=None):
        """
        The event called when the "Show parameters as concatenated query string" checkbox is changed
        """
        # Show the parameter list or query string depending on the option selected
        if self.cbShowQueryString.isSelected():
            self.scroll_outParamList.setViewportView(self.outParamQuery)
        else:
            self.scroll_outParamList.setViewportView(self.outParamList)
        
    def btnHelp_clicked(self, e=None):
        """
        The event when the help icon is pressed. Try to display the Help page, but if the URL can't be reached, show a 404 message
        """
        jpane = JEditorPane()
        jpane.setEditable(False)
        try:
            # Workaround to display text correctly
            jpane2 = JEditorPane()
            jpane2.setPage(GAP_HELP_URL_BUTTON)
            text = jpane2.getText()
            jpane.setContentType("text/html")
            jpane.setText(text)
        except:
            jpane.setContentType("text/html")
            jpane.setText(GAP_HELP_404)
        jpane.setCaretPosition(0)
        jscroll = JScrollPane(jpane)
        jframe = JFrame("GAP Help")
        jframe.getContentPane().add(jscroll)
        jframe.setSize(800, 600)
        jframe.setLocationRelativeTo(None)
        # jframe.setResizable(False)
        jframe.setVisible(True)

        # Try to set the icon of the displayed pane
        try:
            imageUrl = URL(HELP_ICON)
            img = ImageIcon(imageUrl)
            jframe.setIconImage(img.getImage())
        except Exception as e:
            pass

    def btnChooseDir_clicked(self, e=None):
        """
        The event called when the "Choose..." directory button is clicked for the auto save path
        """
        # Show the directory choosing dialog box
        try:
            parentFrame = JFrame()
            dirChooser = JFileChooser()
            dirChooser.setDialogTitle("Choose GAP file output directory:")
            try:
                imageUrl = URL(DIR_ICON)
                img = ImageIcon(imageUrl)
                parentFrame.setIconImage(img.getImage())
            except:
                pass
            dirChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
            # Set the dialogs initial directory to the one displayed.
            try:
                dirChooser.setCurrentDirectory(File(self.inSaveDir.text))
            except:
                # If the displayed directory is no longer valid, start at the users home directory
                dirChooser.setCurrentDirectory(File("~"))
            userSelection = dirChooser.showOpenDialog(parentFrame)

            # Set the displayed save directory to the one selected
            if userSelection == JFileChooser.APPROVE_OPTION:
                self.inSaveDir.text = dirChooser.getSelectedFile().toString()

        except Exception as e:
            self._stderr.println("btnChooseDir_clicked 1")
            self._stderr.println(e)

    def setEnabledParamOptions(self, enabled):
        """
        Called when the "Parameters" check box is changed.
        It will enable/disable all options relating to Parameters.
        """
        # Enable/disable all Parameter options
        try:
            self.cbParamUrl.setEnabled(enabled)
            self.lblRequestParams.setEnabled(enabled)
            self.cbParamBody.setEnabled(enabled)
            self.cbParamMultiPart.setEnabled(enabled)
            self.cbParamJson.setEnabled(enabled)
            self.cbParamCookie.setEnabled(enabled)
            self.cbParamXml.setEnabled(enabled)
            self.cbParamXmlAttr.setEnabled(enabled)
            self.lblQueryStringVal.setEnabled(enabled)
            self.cbShowQueryString.setEnabled(enabled)
            self.inQueryStringVal.setEnabled(enabled)
            self.cbIncludeCommonParams.setEnabled(enabled)
            self.cbIncludePathWords.setEnabled(enabled)
            self.lblResponseParams.setEnabled(enabled)
            self.cbParamJSONResponse.setEnabled(enabled)
            self.cbParamXMLResponse.setEnabled(enabled)
            self.cbParamInputField.setEnabled(enabled)
            self.cbParamJSVars.setEnabled(enabled)
            self.cbParamMetaName.setEnabled(enabled)
            if self.cbLinksEnabled.isSelected():
                self.cbParamFromLinks.setEnabled(enabled)
            else:
                self.cbParamFromLinks.setEnabled(False)
        except Exception as e:
            self._stderr.println("setEnabledParamOptions 1")
            self._stderr.println(e)

    def setEnabledLinkOptions(self, enabled):
        """
        Called when the "Links" check box is changed.
        It will enable/disable all options relating to Links.
        """
        # Enable/disable all Link options
        try:
            self.cbSiteMapEndpoints.setEnabled(enabled)
            self.cbShowLinkOrigin.setEnabled(enabled)
            self.cbInScopeOnly.setEnabled(enabled)
            self.btnFilter.setEnabled(enabled)
            self.lblLinkFilter.setEnabled(enabled)
            self.inLinkFilter.setEnabled(enabled)
            self.cbLinkFilterNeg.setEnabled(enabled)
            self.cbLinkCaseSens.setEnabled(enabled)
            self.inExclusions.setEnabled(enabled)
            self.cbLinkPrefix.setEnabled(enabled)
            self.inLinkPrefix.setEnabled(enabled)
            self.cbUnPrefixed.setEnabled(enabled)
            self.lblExclusions.setEnabled(enabled)
            self.inExclusions.setEnabled(enabled)
            if self.cbParamsEnabled.isSelected():
                self.cbParamFromLinks.setEnabled(enabled)
            else:
                self.cbParamFromLinks.setEnabled(False)
        except Exception as e:
            self._stderr.println("setEnabledLinkOptions 1")
            self._stderr.println(e)

    def setEnabledWordOptions(self, enabled):
        """
        Called when the "Words" check box is changed.
        It will enable/disable all options relating to Words.
        """
        # Enable/disable all Words options
        try:
            self.cbWordParams.setEnabled(enabled)
            self.cbWordComments.setEnabled(enabled)
            self.cbWordDigits.setEnabled(enabled)
            self.cbWordImgAlt.setEnabled(enabled)
            self.cbWordPaths.setEnabled(enabled)
            self.cbWordPlurals.setEnabled(enabled)
            self.lblWordsMaxLen.setEnabled(enabled)
            self.lblWordsMaxLen2.setEnabled(enabled)
            self.inWordsMaxlen.setEnabled(enabled)
            self.lblStopWords.setEnabled(enabled)
            self.inStopWords.setEnabled(enabled)
        except Exception as e:
            self._stderr.println("setEnabledWordOptions 1")
            self._stderr.println(e)
            
    def setEnabledAll(self, enable):
        """
        Called when the GAP process starts to stop the user changing any options during a run, and then re-enabled after a run is complete
        """
        if _debug:
            print("setEnabledAll started")
        try:
            self.cbLinksEnabled.setEnabled(enable)
            self.cbParamsEnabled.setEnabled(enable)
            self.cbWordsEnabled.setEnabled(enable)
            if self.cbParamsEnabled.isSelected():
                self.setEnabledParamOptions(enable)
            if self.cbLinksEnabled.isSelected():
                self.setEnabledLinkOptions(enable)
            if self.cbWordsEnabled.isSelected():
                self.setEnabledWordOptions(enable)
            self.btnRestoreDefaults.setEnabled(enable)
            self.cbSaveFile.setEnabled(enable)
            self.inSaveDir.setEnabled(enable)
            self.btnChooseDir.setEnabled(enable)
            self.btnSave.setEnabled(enable)
        except Exception as e:
            self._stderr.println("setEnabledAll 1")
            self._stderr.println(e)

    def btnFilter_clicked(self, e=None):
        """
        The event called when the "Apply/Clear filter" button is clicked
        """
        if _debug:
            print("btnFilter_clicked started")
        if self.btnFilter.text == "Apply filter":

            # Clear the current link list and filtered list
            self.outLinkList.text = ""
            self.txtLinksFiltered = ""

            # Determine which text to process
            if self.cbShowLinkOrigin.isSelected():
                if self.cbInScopeOnly.isSelected():
                    txtToProcess = self.txtLinksWithURLInScopeOnly
                else:
                    txtToProcess = self.txtLinksWithURL
            else:
                if self.cbInScopeOnly.isSelected():
                    txtToProcess = self.txtLinksOnlyInScopeOnly
                else:
                    txtToProcess = self.txtLinksOnly

            # Build up the set of links to display
            try:
                # Go through all the lines in the Link text with origin URLs
                for line in txtToProcess.splitlines():
                    # If the Negative match option is selected then...
                    if self.cbLinkFilterNeg.isSelected():
                        # add the line if it does contain the entered filter text
                        if (
                            self.cbLinkCaseSens.isSelected()
                            and not self.inLinkFilter.text in line
                        ) or (
                            not self.cbLinkCaseSens.isSelected()
                            and not self.inLinkFilter.text.lower() in line.lower()
                        ):
                            self.txtLinksFiltered = self.txtLinksFiltered + line + "\n"
                    else:  # else look for positive match and
                        # add the line if it doesn't contain the entered filter text
                        if (
                            self.cbLinkCaseSens.isSelected()
                            and self.inLinkFilter.text in line
                        ) or (
                            not self.cbLinkCaseSens.isSelected()
                            and self.inLinkFilter.text.lower() in line.lower()
                        ):
                            self.txtLinksFiltered = self.txtLinksFiltered + line + "\n"

            except Exception as e:
                self._stderr.println("btnFilter_clicked 1")
                self._stderr.println(e)

            # Set the link list to the filtered text
            try:
                if self.txtLinksFiltered != "":
                    self.outLinkList.text = self.txtLinksFiltered
                else:
                    self.outLinkList.text = "NO FILTERED LINKS FOUND"
            except Exception as e:
                self._stderr.println("btnFilter_clicked 2")
                self._stderr.println(e)

            # Set the label to show number of filtered links
            self.lblLinkList.text = (
                "Potential links found - "
                + str(self.outLinkList.text.count("\n"))
                + " filtered:"
            )

            # Once the Apply Filter has been pressed it is changed to Clear filter
            self.btnFilter.setText("Clear filter")

        else:  # the buttons caption is "Clear filter"

            try:
                # Clear the filter
                self.inLinkFilter.text = ""
                self.txtLinksFiltered = ""

                # Reset the Link text area depending on the filters selected
                if self.cbShowLinkOrigin.isSelected():
                    if self.cbInScopeOnly.isSelected():
                        self.outLinkList.text = self.txtLinksWithURLInScopeOnly
                    else:
                        self.outLinkList.text = self.txtLinksWithURL
                else:
                    if self.cbInScopeOnly.isSelected():
                        self.outLinkList.text = self.txtLinksOnlyInScopeOnly
                    else:
                        self.outLinkList.text = self.txtLinksOnly

                # Display the number of unique or filtered links, depending on the filters in place
                if str(self.countLinkUnique) == str(self.outLinkList.text.count("\n")):
                    self.lblLinkList.text = (
                        "Potential links found - "
                        + str(self.countLinkUnique)
                        + " unique:"
                    )
                else:
                    self.lblLinkList.text = (
                        "Potential links found - "
                        + str(self.outLinkList.text.count("\n"))
                        + " filtered:"
                    )

                # Change the label back to "Apply filter" and disable the button
                self.btnFilter.setText("Apply filter")
                self.btnFilter.setEnabled(False)

            except Exception as e:
                self._stderr.println("btnFilter_clicked 3")
                self._stderr.println(e)

        # Position the links output at the start again
        self.outLinkList.setCaretPosition(0)

    def btnSave_clicked(self, e=None):
        """
        The event called when the "Save options" button is clicked
        """
        self.saveConfig()

    def checkLinkPrefix(self):
        """
        Check the Link Prefix is a valid URL
        """
        try:
            invalid = False
            if self.cbLinkPrefix.isSelected():
                result = urlparse(self.inLinkPrefix.text)
                if result.netloc == "":
                    # If prefix doesn't start with // then add http://
                    if result.scheme == "" and self.inLinkPrefix.text[:2] != "//":
                        self.inLinkPrefix.text = "http://" + self.inLinkPrefix.text
                    invalid = True
        
            # Set visibility of warning
            self.lblPrefixWarning.setVisible(invalid)
        except Exception as e:
            self._stderr.println("checkLinkPrefix 1")
            self._stderr.println(e)
            
    def checkMaxWordsLen(self):
        """
        Check the Max Words Length field and change if necessary
        """
        
        # If the maximum word length isn't a number, then set back to default
        if not self.inWordsMaxlen.text.isdigit():
            self.inWordsMaxlen.text = DEFAULT_MAX_WORD_LEN
        else:
            # else if it is a number, but less that 3, set it to 3
            try:
                if int(self.inWordsMaxlen.text) < 3:
                    self.inWordsMaxlen.text = "3"
            except:
                self.inWordsMaxlen.text = DEFAULT_MAX_WORD_LEN
                
    def saveConfig(self):
        """
        Save the options selected to the config
        """
        # Save the autosave output directory used, IF it is real directory
        try:
            # If its a real directory, the following line will not fail
            listOfFile = os.listdir(self.inSaveDir.text)
            # Leave the value as it is
        except:
            # It wasn't a real directory, so set it back to Home directory
            self.inSaveDir.text = self.getDefaultSaveDirectory()

        # Check the words max length in case we need to change it first
        self.checkMaxWordsLen()
        
        # Check the link prefix if option selected
        if self.cbLinkPrefix.isSelected():
            self.checkLinkPrefix()
                 
        # Save the config
        config = {
            "saveFile": self.cbSaveFile.isSelected(),
            "paramUrl": self.cbParamUrl.isSelected(),
            "paramBody": self.cbParamBody.isSelected(),
            "paramMultiPart": self.cbParamMultiPart.isSelected(),
            "paramJson": self.cbParamJson.isSelected(),
            "paramCookie": self.cbParamCookie.isSelected(),
            "paramXml": self.cbParamXml.isSelected(),
            "paramXmlAttr": self.cbParamXmlAttr.isSelected(),
            "includeCommonParams": self.cbIncludeCommonParams.isSelected(),
            "includePathWords": self.cbIncludePathWords.isSelected(),
            "paramJsonResponse": self.cbParamJSONResponse.isSelected(),
            "paramXmlResponse": self.cbParamXMLResponse.isSelected(),
            "paramInputField": self.cbParamInputField.isSelected(),
            "paramJSVars": self.cbParamJSVars.isSelected(),
            "paramMetaName": self.cbParamMetaName.isSelected(),
            "saveDir": self.inSaveDir.text,
            "paramFromLinks": self.cbParamFromLinks.isSelected(),
            "linkExclusions": self.inExclusions.text,
            "showLinkOrigin": self.cbShowLinkOrigin.isSelected(),
            "inScopeOnly": self.cbInScopeOnly.isSelected(),
            "sitemapEndpoints": self.cbSiteMapEndpoints.isSelected(),
            "paramsEnabled": self.cbParamsEnabled.isSelected(),
            "linksEnabled": self.cbLinksEnabled.isSelected(),
            "linkPrefixChecked": self.cbLinkPrefix.isSelected(),
            "linkPrefix": self.inLinkPrefix.text,
            "unprefixed": self.cbUnPrefixed.isSelected(),
            "wordsEnabled": self.cbWordsEnabled.isSelected(),
            "wordPlurals": self.cbWordPlurals.isSelected(),
            "wordPaths": self.cbWordPaths.isSelected(),
            "wordParams": self.cbWordParams.isSelected(),
            "wordDigits": self.cbWordDigits.isSelected(),
            "wordComments": self.cbWordComments.isSelected(),
            "wordImgAlt": self.cbWordImgAlt.isSelected(),
            "wordMaxLen": self.inWordsMaxlen.text,
            "stopWords": self.inStopWords.text          
        }
        self._callbacks.saveExtensionSetting("config", pickle.dumps(config))

    def restoreSavedConfig(self):
        """
        Loads the saved config options
        """
        # Get saved config
        storedConfig = self._callbacks.loadExtensionSetting("config")
        if storedConfig != None:
            try:
                config = pickle.loads(storedConfig)
                self.cbSaveFile.setSelected(config["saveFile"])
                self.cbParamUrl.setSelected(config["paramUrl"])
                self.cbParamBody.setSelected(config["paramBody"])
                self.cbParamMultiPart.setSelected(config["paramMultiPart"])
                self.cbParamJson.setSelected(config["paramJson"])
                self.cbParamCookie.setSelected(config["paramCookie"])
                self.cbParamXml.setSelected(config["paramXml"])
                self.cbParamXmlAttr.setSelected(config["paramXmlAttr"])
                try:
                    self.inQueryStringVal.text = config["queryStringVal"]
                except:
                    self.inQueryStringVal.text = DEFAULT_QSV
                self.cbIncludeCommonParams.setSelected(config["includeCommonParams"])
                self.cbIncludePathWords.setSelected(config["includePathWords"])
                self.cbParamJSONResponse.setSelected(config["paramJsonResponse"])
                self.cbParamXMLResponse.setSelected(config["paramXmlResponse"])
                self.cbParamInputField.setSelected(config["paramInputField"])
                self.cbParamJSVars.setSelected(config["paramJSVars"])
                self.cbParamMetaName.setSelected(config["paramMetaName"])
                try:
                    self.inSaveDir.text = config["saveDir"]
                    # Check the directory is valid, otherwise an error will be raised and it will be reset to default
                    listOfFile = os.listdir(self.inSaveDir.text)
                except:
                    self.inSaveDir.text = self.getDefaultSaveDirectory()
                self.cbParamFromLinks.setSelected(config["paramFromLinks"])
                self.inExclusions.text = config["linkExclusions"]
                self.cbShowLinkOrigin.setSelected(config["showLinkOrigin"])
                self.cbInScopeOnly.setSelected(config["inScopeOnly"])
                self.cbSiteMapEndpoints.setSelected(config["sitemapEndpoints"])
                self.cbParamsEnabled.setSelected(config["paramsEnabled"])
                self.cbLinksEnabled.setSelected(config["linksEnabled"])
                self.cbLinkPrefix.setSelected(config["linkPrefixChecked"])
                try:
                    self.inLinkPrefix.text = config["linkPrefix"]
                except:
                    self.inLinkPrefix.text = DEFAULT_LINK_PREFIX
                self.cbUnPrefixed.setSelected(config["unprefixed"])
                self.cbWordsEnabled.setSelected(config["wordsEnabled"])
                self.cbWordPlurals.setSelected(config["wordPlurals"])
                self.cbWordPaths.setSelected(config["wordPaths"])
                self.cbWordDigits.setSelected(config["wordDigits"])
                self.cbWordParams.setSelected(config["wordParams"])
                self.cbWordComments.setSelected(config["wordComments"])
                self.cbWordImgAlt.setSelected(config["wordImgAlt"])
                self.inWordsMaxlen.text = (config["wordMaxLen"])
                try:
                    self.inStopWords.text = (config["stopWords"])
                except:
                    self.inStopWords.text = DEFAULT_STOP_WORDS
                # Check the words max length in case we need to change it first
                self.checkMaxWordsLen()
                # Check the link prefix is a valid url
                self.checkLinkPrefix()
            except Exception as e:
                # An error will occur the first time used if no settings have been saved.
                # The default settings will be used instead
                pass
        
            # if the link exclusions setting doesn't exist, set it to default
            if self.inExclusions.text == "":
                self.inExclusions.text = DEFAULT_EXCLUSIONS
            
            # If the query string param value doesn't exist, set it to the default
            if self.inQueryStringVal.text == "":
                self.inQueryStringVal.text = DEFAULT_QSV
            
            # if the stop words setting doesn't exist, set it to default
            if self.inStopWords.text == "":
                self.inStopWords.text = DEFAULT_STOP_WORDS
        
        else:
            # If config doesn't exist then restore defaults
            self.btnRestoreDefaults_clicked()
            
            
    def btnRestoreDefaults_clicked(self, e=None):
        """
        The event called when the "Restore defaults" button is clicked.
        Restore the default config options
        """
        # Re-enable all Param options
        self.setEnabledParamOptions(True)

        # Re-enable all Link options
        self.setEnabledLinkOptions(True)
        
        # Re-enable all Word options
        self.setEnabledWordOptions(True)

        # Reset config values
        self.cbSaveFile.setSelected(True)
        self.cbParamUrl.setSelected(True)
        self.cbParamBody.setSelected(True)
        self.cbParamMultiPart.setSelected(True)
        self.cbParamJson.setSelected(False)
        self.cbParamJSONResponse.setSelected(False)
        self.cbParamXMLResponse.setSelected(False)
        self.cbParamInputField.setSelected(False)
        self.cbParamCookie.setSelected(False)
        self.cbParamXml.setSelected(False)
        self.cbParamXmlAttr.setSelected(False)
        self.cbShowQueryString.setSelected(False)
        self.inQueryStringVal.text = DEFAULT_QSV
        self.cbIncludeCommonParams.setSelected(True)
        self.cbIncludePathWords.setSelected(False)
        self.cbParamJSVars.setSelected(False)
        self.cbParamMetaName.setSelected(False)
        self.inSaveDir.text = self.getDefaultSaveDirectory()
        self.cbParamFromLinks.setSelected(False)
        self.inExclusions.text = DEFAULT_EXCLUSIONS
        self.cbShowLinkOrigin.setSelected(False)
        self.cbInScopeOnly.setSelected(False)
        self.cbSiteMapEndpoints.setSelected(False)
        self.cbParamsEnabled.setSelected(True)
        self.cbLinksEnabled.setSelected(True)
        self.cbLinkPrefix.setSelected(False)
        self.cbUnPrefixed.setSelected(False)
        self.inLinkPrefix.text = DEFAULT_LINK_PREFIX
        self.cbWordsEnabled.setSelected(True)
        self.cbWordPlurals.setSelected(True)
        self.cbWordPaths.setSelected(False)
        self.cbWordParams.setSelected(False)
        self.cbWordComments.setSelected(True)
        self.cbWordImgAlt.setSelected(True)
        self.cbWordDigits.setSelected(True)
        self.inWordsMaxlen.text = DEFAULT_MAX_WORD_LEN
        self.inStopWords.text = DEFAULT_STOP_WORDS
        self.saveConfig

    def createMenuItems(self, context):
        """
        Invokes the Extensions "GAP" menu.
        """
        self.context = context
        if context.getInvocationContext() == context.CONTEXT_TARGET_SITE_MAP_TREE:
            menuList = ArrayList()
            menuGAP = JMenuItem("GAP", actionPerformed=self.menuGAP_clicked)
            menuList.add(menuGAP)
            return menuList

    def menuGAP_clicked(self, e=None):
        """
        The event called when the Extensions -> GAP option is selected
        """
        if _debug:
            print("menuGAP_clicked started")

        try:
            # Check the words max length in case we need to change it first
            self.checkMaxWordsLen()
            
            # Check the link prefix is valid
            self.checkLinkPrefix()
        
            # If the user has run GAP, but it is already running then cancel the previous run
            if not self.flagCANCEL and self.btnCancel.text.find("CANCEL GAP") >= 0:
                self.btnCancel_clicked()
            # If the previous run is currently being cancelled, then wait until is had completely ended
            waiting = 0
            while self.flagCANCEL:
                waiting = waiting + 1
                time.sleep(0.2)
                # If 3 seconds has passed then just break and start the new run
                if waiting == 15:
                    break

            # Initialize
            self.roots.clear()
            self.param_list = set()
            self.link_list = set()
            self.linkUrl_list = set()
            self.word_list = set()
            self.txtLinksOnly = ""
            self.txtLinksWithURL = ""
            self.txtLinksOnlyInScopeOnly = ""
            self.txtLinksWithURLInScopeOnly = ""
            self.inLinkFilter.text = ""
            self.btnFilter.text = "Apply filter"

            # Disable all fields so user can't make changes during a run
            self.setEnabledAll(False)

            # Show the CANCEL button
            self.flagCANCEL = False
            self.btnCancel.setText("   CANCEL GAP   ")
            self.btnCancel.setVisible(True)
            self.btnCancel.setEnabled(True)

            # Before starting the search, update the text boxes depending on the options selected
            if self.cbParamsEnabled.isSelected():
                self.lblParamList.text = "Potential parameters found - SEARCHING..."
                self.outParamList.text = "SEARCHING..."
            else:
                self.lblParamList.text = "Potential parameters found:"
                self.outParamList.text = ""
            if self.cbLinksEnabled.isSelected():
                self.lblLinkList.text = "Potential links found - SEARCHING..."
                self.outLinkList.text = "SEARCHING..."
            else:
                self.lblLinkList.text = "Potential links found:"
                self.outLinkList.text = ""
            if WORDLIST_IMPORT_ERROR != "":
                self.lblWordList.text = "Words found - UNAVAILABLE:"
                self.outWordList.text = WORDLIST_IMPORT_ERROR
            else:
                if self.cbWordsEnabled.isSelected():
                    self.lblWordList.text = "Words found - SEARCHING..."
                    self.outWordList.text = "SEARCHING..."
                else:
                    self.lblWordList.text = "Words found:"
                    self.outWordList.text = ""

            # Run everything in a thread so it doesn't freeze Burp while it gets everything
            t = threading.Thread(target=self.doEverything, args=[])
            t.daemon = True
            t.start()
            if _debug:
                print("menuGAP_clicked thread started")

        except Exception as e:
            self._stderr.println("menuGAP_clicked 1")
            self._stderr.println(e)

    def getSiteMapLinks(self, http_message):
        """
        Add site map links if required
        """
        try:
            if _debug:
                print("getSiteMapLinks started")

            http_response = http_message.getResponse()
            if http_response:
                response = self._helpers.analyzeResponse(http_response)
                body_offset = response.getBodyOffset()
                response_string = self._helpers.bytesToString(http_response)
                header = response_string[:body_offset]

                url = http_message.getUrl().toString()
                urlNoQS = url
                if urlNoQS.find("?") >= 0:
                    urlNoQS = urlNoQS[0 : urlNoQS.find("?")]
                if len(url) > 0:

                    # Check link against list of exclusions
                    if self.includeLink(url):

                        # If it is content-type we want to process then carry on
                        if self.includeContentType(header, url):

                            # Only process links that are in scope
                            if self.isLinkInScope(url):

                                # Add the link to the list
                                if _debug:
                                    print(
                                        "getSiteMapLinks link added: "
                                        + url.encode("UTF-8")
                                    )
                                    
                                self.addLink(url)
                                self.addLink(url,urlNoQS)
        except Exception as e:
            self._stderr.println("getSiteMapLinks 1")
            self._stderr.println(e)

    def doEverything(self):
        """
        The methods run in a separate thread when the GAP menu item has been clicked.
        Obtains the selected messages from the interface. Filters the sitemap for all messages containing
        URLs within the selected messages' hierarchy. If so, the message is analyzed to create a parameter list.
        """
        if _debug:
            print("doEverything started")

        # If the user selected the "Include the list of common params in list" option, loads
        # the params in the COMMON_PARAMS value to appear in the final list
        if self.cbIncludeCommonParams.isSelected() == True:
            self.param_list = set(COMMON_PARAMS)
        else:
            self.param_list = set()

        # Get all first-level selected messages and store the URLs as roots to filter the sitemap
        try:
            http_messages = self.context.getSelectedMessages()
            for http_message in http_messages:
                # Need to strip the port from the URL before searching because it _callbacks.getSiteMap fails with older versions of Burp if you don't
                result = urlparse(http_message.getUrl().toString())
                root = result.scheme + "://" + result.netloc.split(":")[0]
                self.roots.add(root)
                self.checkIfCancel()

            # Get all sitemap entries associated with the selected messages and scrape them for parameters, links and words
            currentRoot = 0
            totalRoots = len(self.roots)
            for root in self.roots:
                self.checkIfCancel()
                
                # Change the Progress bar
                noOfMsgs = len(self._callbacks.getSiteMap(root))
                self.progBar.setValue(0)
                self.progBar.setMaximum(noOfMsgs)
                self.progBar.setVisible(True)
                
                # Change the Progress Stage 
                currentRoot = currentRoot + 1
                if totalRoots > 1:
                    self.progStage.text = str(currentRoot) + " / " + str(totalRoots)
                    self.progStage.setVisible(True)
                else:
                    self.progStage.setVisible(False)
                self.progBar.setString("0/" + str(noOfMsgs))
                
                index = 0
                for http_message in self._callbacks.getSiteMap(root):
                    index = index + 1
                    self.progBar.setValue(index)
                    self.progBar.setString(str(index) + "/" + str(noOfMsgs))
                    self.checkIfCancel()
                    url = http_message.getUrl().toString()
                    
                    # Get the links from the site map if the option is selected
                    if self.cbLinksEnabled.isSelected() and self.cbSiteMapEndpoints.isSelected():
                        self.getSiteMapLinks(http_message)

                    # will scrape the same URL multiple times if the site map has stored multiple instances
                    # the site map stores multiple instances if it detects differences, so this is desirable
                    rooturl = urlparse(root)
                    responseurl = urlparse(url)

                    if rooturl.hostname == responseurl.hostname:

                        # If Parameters are enabled
                        if self.cbParamsEnabled.isSelected():

                            # only scrape if there is a request to scrape
                            http_request = http_message.getRequest()
                            if http_request:
                                self.getParams(url, http_request)

                            # Get the response parameters if requested
                            if (
                                self.cbParamJSONResponse.isSelected()
                                or self.cbParamXMLResponse.isSelected()
                                or self.cbParamInputField.isSelected()
                                or self.cbParamJSVars.isSelected()
                                or self.cbParamMetaName.isSelected()
                            ):
                                http_response = http_message.getResponse()
                                if http_response:
                                    self.getResponseParams(http_response)
                                    
                        # Get path words if requested and URL is in scope
                        if (self.cbParamsEnabled.isSelected() and self.cbIncludePathWords.isSelected()) or (self.cbWordsEnabled.isSelected() and self.cbWordPaths.isSelected()):
                            # Try to convert the link to a valid URL object
                            try:
                                inScope = False
                                # The Burp API needs a java.net.URL object to check if it is in scope
                                # Convert the URL. If it isn't a valid URL an exception is thrown so we can catch and not pass to Burp API
                                oUrl = URL(url)
                                if str(oUrl.getHost()) != "":
                                    try:
                                        # If a URL contains invalid characters then Burp raises an error for some reason when _callbacks.isInScope is done, and it can't be caught, so check it's valid
                                        if self.REGEX_BURPURL.search(url) is not None:
                                            inScope = self._callbacks.isInScope(oUrl)
                                        else:
                                            inScope = True
                                    except Exception as e:
                                        # Report as being inScope because we can't be sure if it is or not, but we can include just in case
                                        inScope = True
                            except Exception as e:
                                # The link isn't a valid URL so can't check if it is in scope.
                                inScope = True

                            # Get path words if URL is in scope
                            if inScope:
                                self.getPathWords(responseurl)
                                
                        # If Links are enabled
                        if self.cbLinksEnabled.isSelected():

                            # Get links
                            http_response = http_message.getResponse()
                            if http_response:
                                # Get the response url
                                try:
                                    responseUrl = (
                                        http_message.getUrl().toString().encode("UTF-8")
                                    )
                                except Exception as e:
                                    responseUrl = "ERROR OCCURRED"
                                    self._stderr.println(e)

                                # Get all the links for the current endpoint
                                self.getResponseLinks(http_response, responseUrl)
                                
                        # If the words mode is enabled then search response for words
                        try:
                            if self.cbWordsEnabled.isSelected():
                                http_response = http_message.getResponse()
                                    # Get the response url
                                try:
                                    responseUrl = (
                                        http_message.getUrl().toString().encode("UTF-8")
                                    )
                                except Exception as e:
                                    responseUrl = "ERROR OCCURRED"
                                    self._stderr.println(e)
                                if http_response:
                                    self.getResponseWords(http_response, responseUrl)
                        except Exception as e:
                            self._stderr.println("doEverything 2")
                            self._stderr.println(e)

            # Get the full path of the file
            filepath = self.getFilePath(root)
            
            # Change the Progress bar
            self.progBar.setValue(0)
            maxValue = 0
            if self.cbParamsEnabled.isSelected():
                maxValue = maxValue + 1
            if self.cbLinksEnabled.isSelected():
                maxValue = maxValue + 1
            if self.cbWordsEnabled.isSelected():
                maxValue = maxValue + 1
            self.progBar.setMaximum(maxValue)
            self.progBar.setString("Processing...")
            
            # Display the parameters and links that are found
            self.checkIfCancel()
            self.displayResults(filepath)

            # Change button to completed
            self.checkIfCancel()
            self.btnCancel.setEnabled(False)
            self.btnCancel.setText("   COMPLETED    ")
            self.progBar.setString("100%")
            self.progStage.text = ""

        except CancelGAPRequested as e:
            # The user pressed the CANCEL GAP button
            self.flagCANCEL = False
            if _debug:
                print("doEverything GAP cancelled")
            self.btnCancel.setEnabled(False)
            self.btnCancel.setText("   CANCELLED    ")
            if (
                self.lblParamList.text.find("UPDATING") >= 0
                or self.lblParamList.text.find("SEARCHING") >= 0
                or self.lblParamList.text.find("PROCESSING") >= 0
            ):
                self.lblParamList.text = "Potential parameters found - CANCELLED"
            if (
                self.lblLinkList.text.find("UPDATING") >= 0
                or self.lblLinkList.text.find("SEARCHING") >= 0
                or self.lblLinkList.text.find("PROCESSING") >= 0
            ):
                self.lblLinkList.text = "Potential links found - CANCELLED"
            if (
                self.lblWordList.text.find("UPDATING") >= 0
                or self.lblWordList.text.find("SEARCHING") >= 0
                or self.lblWordList.text.find("PROCESSING") >= 0
            ):
                self.lblWordList.text = "Words found - CANCELLED"
            if self.outParamList.text == "SEARCHING...":
                self.outParamList.text = "CANCELLED"
            if self.outLinkList.text == "SEARCHING...":
                self.outLinkList.text = "CANCELLED"
            if self.outWordList.text == "SEARCHING...":
                self.outWordList.text = "CANCELLED"

        except Exception as e:
            self._stderr.println("doEverything 1")
            self._stderr.println(e)

        # Re-enable all fields now the run has finished
        self.setEnabledAll(True)

    def btnCancel_clicked(self, e=None):
        """
        The event for the CANCEL GAP button
        """
        self.flagCANCEL = True
        self.btnCancel.setText(" CANCELLING...  ")

    def getParams(self, url, http_request):
        """
        Get all the parameters and add them to the param_list set.
        """
        try:
            if _debug:
                print("getParams started")
            request = self._helpers.analyzeRequest(http_request)
            parameters = request.getParameters()[0:]
            for param in parameters:
                # If the parameter is of the type we want to log then get them
                if (
                    (param.getType() == PARAM_URL and self.cbParamUrl.isSelected())
                    or (param.getType() == PARAM_BODY and self.cbParamBody.isSelected())
                    or (
                        param.getType() == PARAM_MULTIPART_ATTR
                        and self.cbParamMultiPart.isSelected()
                    )
                    or (param.getType() == PARAM_JSON and self.cbParamJson.isSelected())
                    or (
                        param.getType() == PARAM_COOKIE
                        and self.cbParamCookie.isSelected()
                    )
                    or (param.getType() == PARAM_XML and self.cbParamXml.isSelected())
                    or (
                        param.getType() == PARAM_XML_ATTR
                        and self.cbParamXmlAttr.isSelected()
                    )
                ):
                    self.addParameter(param.getName().strip())
        except Exception as e:
            self._stderr.println("getParams 1")
            self._stderr.println(e)

    def getDefaultSaveDirectory(self):
        """
        If the directory for saved output data isn't valid this will set the default
        """
        # If on Windows then change the file path to the users Documents directory
        # otherwise it will just be in the users home directory
        try:
            osType = System.getProperty("os.name").lower()
            if osType.find("windows") >= 0:
                directory = os.path.expanduser("~") + "\\Documents\\"
            else:
                directory = os.path.expanduser("~")
        except:
            # If an error occurs, just default to '~/'
            directory = "~/"

        return directory

    def getFilePath(self, rootname):
        """
        Determine the full path of the output file
        """
        # Use the target domain in the filename
        filename = urlparse(rootname).hostname
        
        osType = System.getProperty("os.name").lower()
        if osType.find("windows") >= 0:
            filepath = self.inSaveDir.text + "\\" + filename + "_GAP"
        else:
            filepath = self.inSaveDir.text + "/" + filename + "_GAP"

        return filepath

    def isLinkInScope(self, link):
        """
        Determines whether the link passed in In Scope according to the Burp API
        """
        # Check if the link may need to be excluded if it is not in scope
        # See if it has already been found first
        try:
            # If the link contains the origin endpoint, then strip that
            if link.find("[") >= 0:
                link = link[0 : link.find("[")]
            # If the link contains anything in brackets, then strip that
            if link.find("(") >= 0:
                link = link[0 : link.find("(")]
            if link.find("{") >= 0:
                link = link[0 : link.find("{")]

            # Get from the dictionary
            try:
                newLink = link
                # If the link starts with // then add a protocol just so we can get the potential
                # host to be able to check if it's in scope using the Burp API later
                if newLink.startswith("//"):
                    newLink = "http:" + newLink
                host = URL(newLink).getHost()
                # If we could get a host, get that to the dictionary
                inCheckedLinks = self.dictCheckedLinks.get(host)
            except:
                # If we can't get the host, get the link to the dictionary
                host = ""
                inCheckedLinks = self.dictCheckedLinks.get(link)

            if not inCheckedLinks is None:
                # If found then return the result and don't process further
                inScope = bool(inCheckedLinks)
                return inScope
        except Exception as e:
            self._stderr.println("isLinkInScope 1")
            self._stderr.println(e)

        # Check if the links host is in the selected scope
        inScope = True
        try:
            # If the link has a host (from URL.getHost) and at least one full stop then process further
            if host != "" and host.find(".") >= 0:

                # Initially assume the URL is NOT in scope
                inScope = False

                # From the extracted text, prepend http:// and then check if that is in scope
                try:
                    url = "http://" + host.replace("*.", "")
                    url = "http://" + host.replace("*", "")
                    try:
                        # The Burp API needs a java.net.URL object to check if it is in scope
                        # Convert the URL. If it isn't a valid URL an exception is thrown so we can catch and not pass to Burp API
                        oUrl = URL(url)
                        if str(oUrl.getHost()) != "":
                            try:
                                # If a URL contains invalid characters then Burp raises an error for some reason when _callbacks.isInScope is done, and it can't be caught, so check it's valid
                                if self.REGEX_BURPURL.search(url) is not None:
                                    inScope = self._callbacks.isInScope(oUrl)
                                else: 
                                    inScope = True
                            except Exception as e:
                                # Report as being inScope because we can't be sure if it is or not, but we can include just in case
                                inScope = True
                    except Exception as e:
                        # Report as being inScope because we can't be sure if it is or not, but we can include just in case
                        inScope = True

                except Exception as e:
                    self._stderr.println("isLinkInScope 2")
                    self._stderr.println(e)
                    inScope = True

        except Exception as e:
            self._stderr.println("isLinkInScope 3")
            self._stderr.println(e)

        # Add to the dictionary of links already checked so we don't need to process it again
        try:
            if host == "":
                self.dictCheckedLinks.update({link: inScope})
            else:
                self.dictCheckedLinks.update({host: inScope})
        except Exception as e:
            self._stderr.println("isLinkInScope 4")
            self._stderr.println(e)

        return inScope

    def displayResults(self, filepath):
        """
        Displays the parameter, links and words information retrieved
        """
        if _debug:
            print("displayResults started")

        # Before starting the results, update the text boxes depending on the options selected
        if self.cbParamsEnabled.isSelected():
            self.lblParamList.text = "Potential parameters found - PROCESSING..."
            self.outParamList.text = "PROCESSING..."
        if self.cbLinksEnabled.isSelected():
            self.lblLinkList.text = "Potential links found - PROCESSING..."
            self.outLinkList.text = "PROCESSING..."
        if WORDLIST_IMPORT_ERROR == "":
            if self.cbWordsEnabled.isSelected():
                self.lblWordList.text = "Words found - PROCESSING..."
                self.outWordList.text = "PROCESSING..."
    
        # Start a separate thread for Params, Links and Words
        try:
            if self.cbParamsEnabled.isSelected():
                self.outParamList.text = ""
                tParams = threading.Thread(target=self.displayParams, args=[filepath])
                tParams.daemon = True
                tParams.start()
                tParams.join()

            if self.cbLinksEnabled.isSelected():
                self.outLinkList.text = ""
                tLinks = threading.Thread(target=self.displayLinks, args=[filepath])
                tLinks.daemon = True
                tLinks.start()
                tLinks.join()
            
            if self.cbWordsEnabled.isSelected():
                self.outWordList.text = ""
                tLinks = threading.Thread(target=self.displayWords, args=[filepath])
                tLinks.daemon = True
                tLinks.start()
                tLinks.join()

        except Exception as e:
            self._stderr.println("displayResults 1")
            self._stderr.println(e)

    def displayParams(self, filepath):
        """
        This is called as a separate thread from displayResults to display the found parameters
        """
        if _debug:
            print("displayParams started")
        try:
            # List all the params, one per line IF the param are enabled
            if self.cbParamsEnabled.isSelected():
                index = 0
                self.lblParamList.text = (
                    "Potential parameters found - UPDATING, PLEASE WAIT..."
                )

                # Loop through all parameters and build a list and query string
                allParamsList = ""
                allParamsQuery = ""
                for param in sorted(self.param_list):
                    self.checkIfCancel()
                    try:
                        if len(param) > 0:
                            allParamsList = allParamsList + param + "\n"
            
                            # Build a list of parameters in a concatenated string with unique values
                            allParamsQuery = allParamsQuery + param + "=" + self.inQueryStringVal.text + str(index) + "&"
                            index += 1
                    except Exception as e:
                        self._stderr.println("displayParams 2")
                        self._stderr.println(e)
                        
                if allParamsList == "":
                    self.outParamList.text = "NO PARAMETERS FOUND"
                    self.outParamQuery.text = "NO PARAMETERS FOUND"
                else:
                    self.outParamList.text = allParamsList
                    self.outParamQuery.text = allParamsQuery.rstrip('&')
            
                # Show the version that is selected
                if self.cbShowQueryString.isSelected():
                    self.scroll_outParamList.setViewportView(self.outParamQuery)
                else:
                    self.scroll_outParamList.setViewportView(self.outParamList)                    
                
                index = len(self.param_list)
                self.lblParamList.text = (
                    "Potential parameters found - " + str(index) + " unique:"
                )

            # Write the parameters to a file if required
            self.checkIfCancel()
            if self.cbSaveFile.isSelected():
                self.fileWriteParams(filepath)

        except CancelGAPRequested as e:
            if _debug:
                print("displayParams CancelGAPRequested raised")
            raise CancelGAPRequested("User pressed CANCEL GAP button.")
        except Exception as e:
            self._stderr.println("displayParams 1")
            self._stderr.println(e)

        # Change progress bar
        self.progBar.setValue(self.progBar.getValue()+1)
        
    def displayLinks(self, filepath):
        """
        This is called as a separate thread from displayResults to display the found links
        """
        if _debug:
            print("displayLinks started")
        try:
            # List all the links, one per line, if Links are enabled
            if self.cbLinksEnabled.isSelected():
                self.outLinkList.text = ""
                self.countLinkUnique = 0
                index = 0
                for link in sorted(self.link_list):

                    self.checkIfCancel()

                    # Check if the link may need to be excluded if it is not in scope
                    try:
                        includeLink = self.isLinkInScope(link)
                    except Exception as e:
                        includeLink = True
                        self._stderr.println("displayLinks 2")
                        self._stderr.println(e)

                    try:
                        if len(link) > 0:
                            self.txtLinksOnly = self.txtLinksOnly + link + "\n"
                            if includeLink:
                                self.txtLinksOnlyInScopeOnly = (
                                    self.txtLinksOnlyInScopeOnly + link + "\n"
                                )
                            index += 1
                    except Exception as e:
                        self._stderr.println("displayLinks 3")
                        self._stderr.println(e)

                if _debug:
                    print("displayLinks links found " + str(index))

                for link in sorted(self.linkUrl_list):

                    self.checkIfCancel()

                    # Check if the link may need to be excluded if it is not in scope
                    try:
                        includeLink = self.isLinkInScope(link)
                    except Exception as e:
                        includeLink = True
                        self._stderr.println("displayLinks 4")
                        self._stderr.println(e)

                    try:
                        if len(link) > 0:
                            self.txtLinksWithURL = self.txtLinksWithURL + link + "\n"
                            if includeLink:
                                self.txtLinksWithURLInScopeOnly = (
                                    self.txtLinksWithURLInScopeOnly + link + "\n"
                                )
                    except Exception as e:
                        self._stderr.println("displayLinks 5")
                        self._stderr.println(e)

                if _debug:
                    print("displayLinks links with URL done")

                # Show the links (and Origin Endpoints if the checkbox is ticked)
                if self.cbShowLinkOrigin.isSelected():
                    if self.cbInScopeOnly.isSelected():
                        self.outLinkList.text = self.txtLinksWithURLInScopeOnly
                    else:
                        self.outLinkList.text = self.txtLinksWithURL
                else:
                    if self.cbInScopeOnly.isSelected():
                        self.outLinkList.text = self.txtLinksOnlyInScopeOnly
                    else:
                        self.outLinkList.text = self.txtLinksOnly

                self.countLinkUnique = str(index)

                if str(self.countLinkUnique) == str(self.outLinkList.text.count("\n")):
                    self.lblLinkList.text = (
                        "Potential links found - "
                        + str(self.countLinkUnique)
                        + " unique:"
                    )
                else:
                    self.lblLinkList.text = (
                        "Potential links found - "
                        + str(self.outLinkList.text.count("\n"))
                        + " filtered:"
                    )

                self.cbShowLinkOrigin.setVisible(True)
                self.cbInScopeOnly.setVisible(True)

                # If no links were found, write that in the text box
                if self.outLinkList.text == "":
                    self.outLinkList.text = "NO LINKS FOUND"
                    enabled = False
                else:
                    enabled = True
                self.inLinkFilter.setEnabled(enabled)
                self.cbLinkFilterNeg.setEnabled(enabled)
                self.cbLinkCaseSens.setEnabled(enabled)
                self.btnFilter.setEnabled(enabled)
                self.lblExclusions.setEnabled(enabled)
                self.inExclusions.setEnabled(enabled)

            # Write the links to a file if required
            self.checkIfCancel()
            if self.cbSaveFile.isSelected():
                self.fileWriteLinks(filepath)
                 
        except CancelGAPRequested as e:
            if _debug:
                print("displayLinks CancelGAPRequested raised")
            raise CancelGAPRequested("User pressed CANCEL GAP button.")
        except Exception as e:
            self._stderr.println("displayLinks 1")
            self._stderr.println(e)
            
        # Change progress bar
        self.progBar.setValue(self.progBar.getValue()+1)
        
    def displayWords(self, filepath):
        """
        This is called as a separate thread from displayResults to display the found words
        """
        if _debug:
            print("displayWords started")
        if WORDLIST_IMPORT_ERROR != "":
            self.lblWordList.text = "Words found - UNAVAILABLE:"
            self.outWordList.text = WORDLIST_IMPORT_ERROR
            self.outWordList.text = self.outWordList.text + "\nSee Help for more details."
        else:
            try:
                # List all the words, one per line IF the words are enabled
                if self.cbWordsEnabled.isSelected():
                    index = 0
                    self.lblWordList.text = (
                        "Words found - UPDATING, PLEASE WAIT..."
                    )
                    self.outWordList.text = "\n".join(sorted(self.word_list))
                    index = len(self.word_list)
                    self.lblWordList.text = (
                        "Words found - " + str(index) + " unique:"
                    )

                    # If no words were found, write that in the text box
                    if self.outWordList.text == "":
                        self.outWordList.text = "NO WORDS FOUND"

                # Write the words to a file if required
                self.checkIfCancel()
                if self.cbSaveFile.isSelected():
                    self.fileWriteWords(filepath)

            except CancelGAPRequested as e:
                if _debug:
                    print("displayWords CancelGAPRequested raised")
                raise CancelGAPRequested("User pressed CANCEL GAP button.")
            except Exception as e:
                self._stderr.println("displayWords 1")
                self._stderr.println(e)
        
        # Change progress bar
        self.progBar.setValue(self.progBar.getValue()+1)
              
    def fileWriteParams(self, filepath):
        """
        Writes the parameters to a file in the requested directory
        """
        if _debug:
            print("fileWriteParams started")
        try:
            # Write all parameters to a file if any exist and its enabled
            self.checkIfCancel()
            if self.cbParamsEnabled.isSelected():
                if self.outParamList.text != "NO PARAMETERS FOUND":
                    with open(os.path.expanduser(filepath + "_params.txt"), "w") as f:
                        for param in sorted(self.param_list):
                            self.checkIfCancel()
                            try:
                                if param != "":
                                    f.write(param.encode("UTF-8") + "\n")
                            except Exception as e:
                                self._stderr.println("fileWriteParams 1")
                                self._stderr.println(e)

        except IOError as e:
            self._stderr.println("There is a problem with the Save directory " + self.inSaveDir.text + ". Check it and correct it.")
        except CancelGAPRequested as e:
            if _debug:
                print("fileWriteParams CancelGAPRequested raised")
            raise CancelGAPRequested("User pressed CANCEL GAP button.")
        except Exception as e:
            self._stderr.println("fileWriteParams 2")
            self._stderr.println(e)

    def fileWriteLinks(self, filepath):
        """
        Writes the links to a file in the requested directory
        """
        if _debug:
            print("fileWriteLinks started")
        try:
            # Write all links to a file if any exist
            self.checkIfCancel()
            if self.cbLinksEnabled.isSelected():
                if self.outLinkList.text != "NO LINKS FOUND":
                    with open(os.path.expanduser(filepath + "_links.txt"), "w") as f:
                        try:
                            if self.cbShowLinkOrigin.isSelected():
                                if self.cbInScopeOnly.isSelected():
                                    f.write(
                                        self.txtLinksWithURLInScopeOnly.encode("UTF-8")
                                    )
                                else:
                                    f.write(self.txtLinksWithURL.encode("UTF-8"))
                            else:
                                if self.cbInScopeOnly.isSelected():
                                    f.write(
                                        self.txtLinksOnlyInScopeOnly.encode("UTF-8")
                                    )
                                else:
                                    f.write(self.txtLinksOnly.encode("UTF-8"))
                        except Exception as e:
                            self._stderr.println("fileWriteParams 3")
                            self._stderr.println(e)
        except IOError as e:
                self._stderr.println("There is a problem with the Save directory " + self.inSaveDir.text + ". Check it and correct it.")
        except CancelGAPRequested as e:
            if _debug:
                print("fileWriteLinks CancelGAPRequested raised")
            raise CancelGAPRequested("User pressed CANCEL GAP button.")
        except Exception as e:
            self._stderr.println("fileWriteParams 4")
            self._stderr.println(e)

    def fileWriteWords(self, filepath):
        """
        Writes the words to a file in the requested directory
        """
        if _debug:
            print("fileWriteWords started")
        if WORDLIST_IMPORT_ERROR != "":
            self.lblWordList.text = "Words found - UNAVAILABLE:"
            self.outWordList.text = WORDLIST_IMPORT_ERROR
        else:
            try:
                # Write all words to a file if any exist and its enabled
                self.checkIfCancel()
                if self.cbWordsEnabled.isSelected():
                    if self.outWordList.text != "NO WORDS FOUND":
                        with open(os.path.expanduser(filepath + "_words.txt"), "w") as f:
                            for word in sorted(self.word_list):
                                self.checkIfCancel()
                                try:
                                    if word != "":
                                        f.write(word.encode("UTF-8") + "\n")
                                except Exception as e:
                                    self._stderr.println("fileWriteWords 1")
                                    self._stderr.println(e)
                                    
            except IOError as e:
                self._stderr.println("There is a problem with the Save directory " + self.inSaveDir.text + ". Check it and correct it.")
            except CancelGAPRequested as e:
                if _debug:
                    print("fileWriteWords CancelGAPRequested raised")
                raise CancelGAPRequested("User pressed CANCEL GAP button.")
            except Exception as e:
                self._stderr.println("fileWriteWords 2")
                self._stderr.println(e)
            
    def getResponseParams(self, http_response):
        """
        Get XML and JSON responses, extract keys and add them to the param_list
        Original contributor: @_pichik
        In addition it will extract name and id from <input> fields in HTML
        """
        if _debug:
            print("getResponseParams started")
        try:
            response = self._helpers.analyzeResponse(http_response)
            body_offset = response.getBodyOffset()
            response_string = self._helpers.bytesToString(http_response)
            body = response_string[body_offset:]

            # Get regardless of the content type
            # Javascript variable could be in the html, script and even JSON response within a .js.map file
            if self.cbParamJSVars.isSelected():

                # Get inline javascript variables defined with "let"
                try:
                    js_keys = re.finditer(
                        r"(?<=let[\s])[\s]*[a-zA-Z$_][a-zA-Z0-9$_]*[\s]*(?=(\=|;|\n|\r))",
                        body,
                        re.IGNORECASE,
                    )
                    for key in js_keys:
                        if key is not None and key.group() != "":
                            self.addParameter(key.group().strip())
                except Exception as e:
                    self._stderr.println("getResponseParams 1")
                    self._stderr.println(e)

                # Get inline javascript variables defined with "var"
                try:
                    js_keys = re.finditer(
                        r"(?<=var\s)[\s]*[a-zA-Z$_][a-zA-Z0-9$_]*?(?=(\s|=|,|;|\n))",
                        body,
                        re.IGNORECASE,
                    )
                    for key in js_keys:
                        if key is not None and key.group() != "":
                            self.addParameter(key.group().strip())
                except Exception as e:
                    self._stderr.println("getResponseParams 2")
                    self._stderr.println(e)

                # Get inline javascript constants
                try:
                    js_keys = re.finditer(
                        r"(?<=const\s)[\s]*[a-zA-Z$_][a-zA-Z0-9$_]*?(?=(\s|=|,|;|\n))",
                        body,
                        re.IGNORECASE,
                    )
                    for key in js_keys:
                        if key is not None and key.group() != "":
                            self.addParameter(key.group().strip())
                except Exception as e:
                    self._stderr.println("getResponseParams 3")
                    self._stderr.println(e)

            # If mime type is JSON then get the JSON attributes
            if response.getStatedMimeType() == "JSON":
                if self.cbParamJSONResponse.isSelected():
                    try:
                        # Get only keys from json (everything between double quotes:)
                        json_keys = re.findall(
                            '"([a-zA-Z0-9$_\.-]*?)":', body, re.IGNORECASE
                        )
                        for key in json_keys:
                            self.addParameter(key.strip())
                    except Exception as e:
                        self._stderr.println("getResponseParams 4")
                        self._stderr.println(e)

            # If the mime type is XML then get the xml keys
            elif response.getStatedMimeType() == "XML":
                if self.cbParamXMLResponse.isSelected():
                    try:
                        # Get XML attributes
                        xml_keys = re.findall("<([a-zA-Z0-9$_\.-]*?)>", body)
                        for key in xml_keys:
                            self.addParameter(key.strip())
                    except Exception as e:
                        self._stderr.println("getResponseParams 5")
                        self._stderr.println(e)

            # If the mime type is HTML then get <input> name and id values, and meta tag names
            elif response.getStatedMimeType() == "HTML":

                if self.cbParamInputField.isSelected():
                    # Get Input field name and id attributes
                    try:
                        html_keys = re.findall("<input(.*?)>", body)
                        for key in html_keys:
                            input_name = re.search(
                                r"(?<=\sname)[\s]*\=[\s]*(\"|')(.*?)(?=(\"|\'))",
                                key,
                                re.IGNORECASE,
                            )
                            if input_name is not None and input_name.group() != "":
                                input_name_val = input_name.group()
                                input_name_val = input_name_val.replace("=", "")
                                input_name_val = input_name_val.replace('"', "")
                                input_name_val = input_name_val.replace("'", "")
                                self.addParameter(input_name_val.strip())
                            input_id = re.search(
                                r"(?<=\sid)[\s]*\=[\s]*(\"|')(.*?)(?=(\"|'))",
                                key,
                                re.IGNORECASE,
                            )
                            if input_id is not None and input_id.group() != "":
                                input_id_val = input_id.group()
                                input_id_val = input_id_val.replace("=", "")
                                input_id_val = input_id_val.replace('"', "")
                                input_id_val = input_id_val.replace("'", "")
                                self.addParameter(input_id_val.strip())
                    except Exception as e:
                        self._stderr.println("getResponseParams 6")
                        self._stderr.println(e)

                if self.cbParamMetaName.isSelected():
                    # Get meta tag name attribute
                    try:
                        meta_keys = re.findall("<meta(.*?)>", body)
                        for key in meta_keys:
                            meta_name = re.search(
                                r"(?<=\sname)[\s]*\=[\s]*(\"|')(.*?)(?=(\"|'))",
                                key,
                                re.IGNORECASE,
                            )
                            if meta_name is not None and meta_name.group() != "":
                                meta_name_val = meta_name.group()
                                meta_name_val = meta_name_val.replace("=", "")
                                meta_name_val = meta_name_val.replace('"', "")
                                meta_name_val = meta_name_val.replace("'", "")
                                self.addParameter(meta_name_val.strip())
                    except Exception as e:
                        self._stderr.println("getResponseParams 7")
                        self._stderr.println(e)
        except Exception as e:
            self._stderr.println("getResponseParams 8")
            self._stderr.println(e)

    def includeLink(self, link):
        """
        Determine if the passed Link should be excluded by checking the list of exclusions
        Returns whether the link should be included
        """
        include = True

        # Exclude if the finding is an endpoint link but has more than one newline character. This is a false
        # positive that can sometimes be raised by the regex
        # And exclude if the link:
        # - starts with literal characters \n
        # - starts with #
        # - starts with \
        # - has any white space characters in
        # - has any new line characters in
        # - doesn't have any letters or numbers in
        try:
            if link.count("\n") > 1 or link.startswith("#") or link.startswith("$") or link.startswith("\\"):
                include = False
            if include:
                include = not (bool(re.search(r"\s", link)))
            if include:
                include = not (bool(re.search(r"\n", link)))
            if include:
                include = bool(re.search(r"[0-9a-zA-Z]", link))
        except Exception as e:
            self._stderr.println("includeLink 2")
            self._stderr.println(e)

        if include:
            # Get the exclusions
            try:
                lstExclusions = self.inExclusions.text.split(",")
            except:
                self._stderr.println("Exclusion list invalid. Using default list")
                lstExclusions = DEFAULT_EXCLUSIONS.split(",")

            # Go through lstExclusions and see if finding contains any. If not then continue
            # If it fails then try URL encoding and then checking
            linkWithoutQueryString = link.split("?")[0].lower()
            for exc in lstExclusions:
                try:
                    if linkWithoutQueryString.encode(encoding="ascii",errors="ignore").find(exc.lower()) >= 0:
                        include = False
                except Exception as e:
                    include = False
                    self._stderr.println(
                        "includeLink 1: Failed to check exclusions for a finding on URL: "
                        + link
                    )
                    self._stderr.println(e)

        return include

    def includeFile(self, url):
        """
        Determine if the passed should be excluded by checking the list of exclusions
        Returns whether the url should be included
        """
        try:
            include = True
            
            # Set the file extension exclusions
            lstFileExtExclusions = FILEEXT_EXCLUSIONS.split(",")
            
            # Go through FILEEXT_EXCLUSIONS and see if finding contains any. If not then continue
            for exc in lstFileExtExclusions:
                try:
                    if url.endswith(exc.lower()):
                        include = False
                except Exception as e:
                    self._stderr.println("ERROR includeFile 2")
                    self._stderr.println(e)

        except Exception as e:
            self._stderr.println("ERROR includeFile 1")
            self._stderr.println(e)

        return include

    def includeContentType(self, header, url):
        """
        Determine if the content type is in the exclusions
        Returns whether the content type is included
        """
        if _debug:
            print("includeContentType started")
        # Get the content-type from the response
        try:
            contentType = self.REGEX_CONTENTTYPE.findall(header)[0]
            # If content-type is in format like "text/plain; charset=utf-8", then just select the first part
            contentType = contentType.split(";")[0]
        except Exception as e:
            contentType = ""

        # If the content type wasn't found, check against file extensions
        if contentType == "":
            url = url.split("?")[0].split("#")[0].split("/")[-1]
            if url.find(".") > 0:
                include = self.includeFile(url)
            
        # Check the content-type against the comma separated list of exclusions
        lstExcludeContentType = CONTENTTYPE_EXCLUSIONS.split(",")
        include = True
        for excludeContentType in lstExcludeContentType:
            if contentType.lower() == excludeContentType.lower():
                include = False

        return include

    def getResponseLinks(self, http_response, responseUrl):
        """
        Get a list of links found
        """
        if _debug:
            print("getResponseLinks started")

        response = self._helpers.analyzeResponse(http_response)
        body_offset = response.getBodyOffset()
        response_string = self._helpers.bytesToString(http_response)
        body = response_string[body_offset:]
        header = response_string[:body_offset]

        # Some URLs may be displayed in the body within strings that have different encodings of / and : so replace these
        body = re.sub("(&#x2f;|%2f|\\u002f|\\\/)", "/", body, flags=re.IGNORECASE)
        body = re.sub("(&#x3a;|%3a|\\u003a|\\\/)", ":", body, flags=re.IGNORECASE)
        
        # Replace occurrences of HTML entity &quot; with an actual double quote
        body = body.replace('&quot;','"')
        
        try:
            # If it is content-type we want to process then carry on
            if self.includeContentType(header, responseUrl):

                search = header.replace(" ","\n").encode("utf-8")+body.encode("utf-8")
                try:
                    link_keys = self.REGEX_LINKS.finditer(search)
                except Exception as e:
                    self._stderr.println("getResponseParams 4")
                    self._stderr.println(e)
            
                for key in link_keys:
                    if key is not None and len(key.group()) > 1:
                        link = key.group()
                        link = link.strip("\"'\n\r( ")
                        link = link.replace("\\n", "")
                        link = link.replace("\\r", "")
                        link = link.replace("\\.", ".")

                        try:
                            first = link[:1]
                            last = link[-1]
                            firstTwo = link[:2]
                            lastTwo = link[-2]

                            if (
                                first == '"'
                                or first == "'"
                                or first == "\n"
                                or first == "\r"
                                or firstTwo == "\\n"
                                or firstTwo == "\\r"
                            ) and (
                                last == '"'
                                or last == "'"
                                or last == "\n"
                                or last == "\r"
                                or lastTwo == "\\n"
                                or lastTwo == "\\r"
                            ):
                                if firstTwo == "\\n" or firstTwo == "\\r":
                                    start = 2
                                else:
                                    start = 1
                                if lastTwo == "\\n" or lastTwo == "\\r":
                                    end = 2
                                else:
                                    end = 1
                                link = link[start:-end]

                            # If there are any trailing back slashes, comma, ; or >; remove them all
                            link = link.rstrip("\\")
                            link = link.rstrip(">;")
                            link = link.rstrip(";")
                            link = link.rstrip(",")
                            
                            # If there are any backticks in the URL, remove everything from the backtick onwards
                            link = link.split("`")[0]
                            
                            # If there are any closing brackets of any kind without an opening bracket, remove everything from the closing bracket onwards
                            if re.search(r"^[^(]*\)*$",link):
                                link = link.split(")", 1)[0]
                            if re.search(r"^[^{}]*\}*$",link):
                                link = link.split("}", 1)[0]
                            if re.search(r"^[^\[]]*\]*$",link):
                                link = link.split("]", 1)[0]    
                                
                            # If there is a </ in the link then strip from that forward
                            if re.search(r"<\/", link):
                               link = link.split("</", 1)[0]                           
                        
                        except Exception as e:
                            self._stderr.println("getResponseLinks 2")
                            self._stderr.println(e)
                            try:
                                self._stderr.println("The link that caused the error: " + link)
                            except:
                                pass

                        # If the link starts with a . and the  2nd character is not a . or / then remove the first .
                        if link[0] == "." and link[1] != "." and link[1] != "/":
                            link = link[1:]

                        # Determine if Link should be included
                        include = self.includeLink(link)

                        # If the link found is for a .js.map file then put the full .map URL in the list
                        if link.find("//# sourceMappingURL") >= 0:
                            include = True

                            # Get .map link after the =
                            firstpos = link.rfind("=")
                            lastpos = link.find("\n")
                            if lastpos <= 0:
                                lastpos = len(link)
                            mapFile = link[firstpos + 1 : lastpos]

                            # Get the response url up to last /
                            lastpos = responseUrl.rfind("/")
                            mapPath = responseUrl[0 : lastpos + 1]

                            # Add them to get link of js.map and add to list
                            link = mapPath + mapFile
                            link = link.replace("\n", "")

                        # If a link starts with // then add http:
                        if link.startswith("//"):
                            link = "http:" + link

                        # Only add the finding if it should be included
                        if include:
                            self.addLink(link)
                            self.addLink(link,responseUrl)

                            # Get parameters from links if requested, Parameters mode is enabled AND the link is in scope
                            if (
                                self.cbParamFromLinks.isSelected()
                                and self.cbParamsEnabled.isSelected()
                                and link.count("?") > 0
                                and self.isLinkInScope(link)
                            ):
                                # Get parameters from the link
                                try:
                                    link = link.replace("&amp;", "&")
                                    link = link.replace("\\x26", "&")
                                    link = link.replace("\\u0026", "&")
                                    link = link.replace("&equals;", "=")
                                    link = link.replace("\\x3d", "=")
                                    link = link.replace("\\u003d", "=")
                                    param_keys = re.finditer(
                                        r"(?<=\?|&)[^\=\&\n].*?(?=\=|&|\n)", link
                                    )
                                    for param in param_keys:
                                        if param is not None and param.group() != "":
                                            self.addParameter(param.group().strip())
                                except Exception as e:
                                    self._stderr.println("getResponseLinks 3")
                                    self._stderr.println(e)

        except Exception as e:
            self._stderr.println("getResponseLinks 1")
            self._stderr.println(e)
            try:
                self._stderr.println("The link that caused the error: " + link)
            except:
                pass
            
        # Also add a link of a js.map file if the X-SourceMap or SourceMap header exists
        try:
            # See if the SourceMap header exists
            try:
                mapFile = re.findall(
                    r"(?<=SourceMap\:\s).*?(?=\n)", header, re.IGNORECASE
                )[0]
            except:
                mapFile = ""
            # If not found, try the deprecated X-SourceMap header
            if mapFile != "":
                try:
                    mapFile = re.findall(
                        r"(?<=X-SourceMap\:\s).*?(?=\n)", header, re.IGNORECASE
                    )[0]
                except:
                    mapFile = ""
            # If a map file was found in the response, then add a link for it
            if mapFile != "":
                self.addLink(mapFile)
                self.addLink(mapFile,responseUrl)
        except Exception as e:
            self._stderr.println("getResponseLinks 4")
            self._stderr.println(e)

    def getResponseWords(self, http_response, responseUrl):
        """
        Get a list of words found
        """
        if _debug:
            print("getResponseWords started")
        try:
            response = self._helpers.analyzeResponse(http_response)
            body_offset = response.getBodyOffset()
            response_string = self._helpers.bytesToString(http_response)
            body = response_string[body_offset:]
            header = response_string[:body_offset]
            
            # Get the content-type from the response
            try:
                contentType = re.findall(
                    r"(?<=Content-Type\:\s)[a-zA-Z\-].+\/[a-zA-Z\-].+?(?=\s|\;)",
                    header,
                    re.IGNORECASE,
                )[0]
                contentType = contentType.split(";")[0]
            except:
                contentType = ""
            
            # Also get the MIME type so we can compare both
            try:
                mimeType = response.getStatedMimeType()
            except:
                mimeType = ""
                
            # If it's a content type we want to retrieve words from then search
            if mimeType in ("HTML","XML","JSON","PLAIN") or contentType.lower() in DEFAULT_WORDS_CONTENT_TYPES:
                # Parse html content with beautifulsoup4
                # If html5lib is installed then use that as a parser. It is slower than the default, but is more accurate and doesn't throw runtime errors
                allText = ""
                try:
                    if html5libInstalled:
                        soup = BeautifulSoup(body, "html5lib")
                    else:
                        soup = BeautifulSoup(body, "html.parser")
                except Exception as e:
                    self._stderr.println("getResponseWords 2")
                    self._stderr.println(e)
                
                # Get words from meta tag contents
                for tag in soup.find_all("meta", content=True):
                    self.checkIfCancel()
                    if tag.get("property", None) in ["og:title","og:description"] or tag.get("name", None) in ["description","keywords","twitter:title","twitter:description"]:
                        allText = allText + tag['content'] + ' '

                # Get words from any "alt" attribute of images if required
                if self.cbWordImgAlt.isSelected():
                    for img in soup.find_all('img', alt=True):
                        self.checkIfCancel()
                        allText = allText + img['alt'] + ' '

                # Get words from any comments if required
                if self.cbWordComments.isSelected():
                    for comment in soup.findAll(text=lambda text:isinstance(text, Comment)):
                        self.checkIfCancel()
                        allText = allText + comment + ' '
  
                # Remove tags we don't want content from
                for data in soup(['style', 'script', 'link']): 
                    self.checkIfCancel()
                    data.decompose()

                # Get words from the body text
                allText = allText + " ".join(soup.stripped_strings)
                
                # Build list of potential words over 3 characters long
                potentialWords = re.findall(r"[\w']{3,}", allText)
                potentialWords = set(potentialWords) 
                
                # Process all words found
                for word in potentialWords:
                    self.checkIfCancel()
                    # Check if word is not already been found 
                    if word not in self.word_list:
                        # If "Include word with digits" is checked, only proceed with word if it has no digits
                        if not (self.cbWordDigits and any(char.isdigit() for char in word)):
                            if re.search('[a-zA-Z]', word):
                                # strip apostrophes
                                word = word.replace("'", "")
                                # add the word to the list if not a stop word and is not above the max length
                                if len(word) > 0 and word.lower() not in self.lstStopWords and (self.inWordsMaxlen.text == "0" or len(word) <= int(self.inWordsMaxlen.text)):
                                    self.word_list.add(word)
                                    self.word_list.add(word.lower())
                                    # If "Create singluar/plural words" option is checked, check if there is a singular/plural word to add
                                    if self.cbWordPlurals.isSelected():
                                        newWord = self.processPlural(word)
                                        if newWord != "" and len(newWord) > 3 and newWord.lower() not in self.lstStopWords:
                                            self.word_list.add(newWord)
                                            self.word_list.add(newWord.lower())
                                            # If the original word was uppercase and didn't end in "S" but the new one does, also add the original word with a lower case "s"
                                            if word.isupper() and word[-1:] != 'S' and newWord == word + 'S':
                                                self.word_list.add(word + 's')
              
        except Exception as e:
            self._stderr.println("getResponseWords 1")
            self._stderr.println(e)
            try:
                self._stderr.println("The word that caused the error: " + word)
            except:
                pass
            
    def getPathWords(self, url):
        """
        Get all words from path and if they do not contain file extension add them to the param_list
        Original contributor: @_pichik
        """
        if _debug:
            print("getPathWords started")
        try:
            # Split the URL on /
            words = re.compile(r"[\:/?=\-&#]+", re.UNICODE).split(url.path)
            # Add the word to the parameter list, unless it has a . in it or is a number. or it is a single character that isn't a letter
            for word in words:
                if (
                    ("." not in word)
                    and (not word.isnumeric())
                    and not (len(word) == 1 and not word.isalpha())
                    and len(word) > 0
                ):
                    # If path words as Words are required, add to the list of words
                    if self.cbWordsEnabled.isSelected() and self.cbWordPaths.isSelected():
                        self.addWord(word.strip())
                        
                    # If path words as parameters are required, add to the list of parameters
                    if self.cbParamsEnabled.isSelected() and self.cbIncludePathWords.isSelected():
                        self.addParameter(word.strip())
        except Exception as e:
            self._stderr.println("getPathWords 1")
            self._stderr.println(e)

    def checkIfCancel(self):
        if self.flagCANCEL:
            raise CancelGAPRequested("User pressed CANCEL GAP button.")

    def processPlural(self, originalWord):
        """
        A function that attempts to take a given English word, determine if its a plural or singular.
        If a plural, then return a new word as singular. If a singular, then return a new word as plural.
        IMPORTANT: This is prone to error as the english language has many exceptions to rules!
        """
        try:
            newWord = ""
            word = originalWord.strip().lower()
            
            # Process Plurals and get a new word for singular
            
            # If word is over 30 characters long 
            # OR contains numbers and is over 10 characters long
            # OR ends in "ous"
            # then there will not be a new word
            if len(word) > 30 or (any(char.isdigit() for char in word) and len(word) > 10) or word[-4:] == "ous":
                newWord = ""
            # If word ends in "xes", "oes" or "sses" then remove the last "es" for the new word
            elif word[-3:] in ["xes","oes"] or word[-4:] == "sses":
                newWord = originalWord[:-2]
            # If word ends in "ies"
            elif word[-3:] == "ies":
                # If there is 1 letter before "ies" then the new word will just end "ie"
                if len(word) == 4:
                    if originalWord.isupper():
                        newWord = originalWord[1]+"IE"
                    else:
                        newWord = originalWord[1]+"ie"
                else: # the new word will just have "ies" replaced with "y"
                    if originalWord.isupper():
                        newWord = originalWord[:-3]+"Y"
                    else: 
                        newWord = originalWord[:-3]+"y"
            # If the word ends in "s" and isn't proceeded by "s" then the new word will have the last "s" removed
            elif word[-1:] == "s" and word[-2:-1] != "s":
                newWord = originalWord[:-1]
                
            # Process Singular and get a new word for plural
            
            # If word ends in "x","o" or "ss" then add "es" for the new word
            elif word[-1:] in ["x","o"] or word[-2:] == "ss":
                if originalWord.isupper():
                    newWord = originalWord+"ES"
                else:
                    newWord = originalWord+"es"
            # If word ends in "y" and isn't proceeded by a vowel, then replace "y" with "ies" for new word
            elif word[-1:] == "y" and word[-2:-1] not in ["a","e","i","o","u"]:
                if originalWord.isupper():
                    newWord = originalWord[:-1]+"IES"
                else:
                    newWord = originalWord[:-1]+"ies"    
            # If word ends in "o" and not prefixed by a vowel, then add "es" to get a new plural
            elif word[-1:] == "o" and word[-2:-1] not in ["a","e","i","o","u"]:
                if originalWord.isupper():
                    newWord = originalWord[:-1]+"ES"
                else:
                    newWord = originalWord[:-1]+"es"    
            # Else just add an "s" to get a new plural word
            else: 
                if originalWord.isupper():
                    newWord = originalWord+"S"
                else:
                    newWord = originalWord+"s"
            return newWord
        except Exception as e:
            self._stderr.println("processPlural 1")
            self._stderr.println(e)

    def addLink(self, url, origin=""):
        """
        Add a link, and prefix if necessary
        """
        try:
            # If the Link Prefix option is checked, then prefix if the link doesn't have a domain
            if self.cbLinkPrefix.isSelected():
                
                url = url.encode(encoding="ascii",errors="ignore")
                
                # Get the netloc of the url and if blank, add the prefix
                result = urlparse(url)
                if result.netloc == "":
                    # If the "Include un-prefixed links" option is checked,add the original first
                    if self.cbUnPrefixed.isSelected():
                        if origin == "":                                      
                            # Add the link to the list
                            self.link_list.add(url)
                        else:
                            # Add the link and origin to the list
                            self.linkUrl_list.add(url + "  [" + origin + "]")
                    
                    # If the link prefix ends in / then remove it
                    if self.inLinkPrefix.text[-1] == "/":
                        self.inLinkPrefix.text = self.inLinkPrefix.text[:-1]
                    # If the url doesn't start with a / then prefix it first
                    if url[:1] != "/":
                        url = "/" + url
                    # Prefix with the link prefix given
                    url = self.inLinkPrefix.text + url

            if origin == "":                                      
                # Add the link to the list
                self.link_list.add(url)
            else:
                # Add the link and origin to the list
                self.linkUrl_list.add(url + "  [" + origin + "]")
                
        except Exception as e:
            self._stderr.println("addLink 1")
            self._stderr.println(e)
            
    def addParameter(self, param):
        """
        Determine whether to add a parameter to the parameter list, and also to the word list depending on ticked options
        """
        try:
            param = param.encode(encoding="ascii",errors="ignore")

            # Add the parameter to the list
            self.param_list.add(param)

            # If the Words option is checked and the Include parameters is also checked, add the parameter to the word list
            if self.cbWordsEnabled.isSelected() and self.cbWordParams.isSelected():
                self.addWord(param)

        except Exception as e:
            self._stderr.println("addParameter 1")
            self._stderr.println(e)
            
    def addWord(self, word):
        """
        Determine whether to add a word to the wordlist depending on ticked options
        """
        try:
            include = True
            
            word = word.encode(encoding="ascii",errors="ignore")
            
            # Check it is a minimum of 3 characters long
            if len(word.strip()) < 3:
                include = False
                
            # Check if digits
            elif not self.cbWordDigits.isSelected() and re.search(r'\d', word):
                include = False
            
            # Check the word isn't in the Stopword list
            elif word.lower() in self.lstStopWords:
                include = False
                
            # Check word length
            try:
                if include and len(word.strip()) > int(self.inWordsMaxlen.text):
                    include = False
            except:
                pass
                
            # Add the word to the list if it passed the tests
            if include:
                self.word_list.add(word.strip())
                
                # Add a plural or singluar version of the word if required
                if self.cbWordPlurals.isSelected():
                    plural = self.processPlural(word)
                    if plural != "":
                        self.word_list.add(plural)
                
        except Exception as e:
            self._stderr.println("addWord 1")
            self._stderr.println(e)
            
class CancelGAPRequested(Exception):
    pass


class CustomKeyListener(KeyListener):
    """
    A custom event listener used for the "Apply/Clear Filter" button
    """

    def __init__(self, button):
        self.button = button

    def keyTyped(self, e=None):

        # Re-enable the "Apply filter" button
        if ord(e.keyChar) != 10:

            # Clear the current filter
            if self.button.text.startswith("Clear"):
                self.button.doClick()

            # Set the filter back to Apply
            self.button.setText("Apply filter")
            self.button.setEnabled(True)

    def keyPressed(self, e=None):
        # If ENTER pressed and the button is enabled, click it!
        if e.keyCode == 10 and self.button.isEnabled():
            self.button.doClick()

    def keyReleased(self, e=None):
        return
