from deep_translator import GoogleTranslator

lib_js_file_names = [
    "https://cc\.cdn\.civiccomputing\.com/9/cookieControl-9\.x\.min\.js",  # Civic Cookie Control
    "https://cc\.cdn\.civiccomputing\.com/9/cookieControl-9\.5\.min\.js",
    "clickio\.mgr\.consensu\.org/t/consent_225761\.js",  # Clickio Consent Tool
    'window.gdprAppliesGlobally=true;if(!("cmp_id" in window)||window.cmp_id<1){window.cmp_id=0}if(!("cmp_cdid" in window))'
    '{window.cmp_cdid="3834f5ec2941"}if(!("cmp_params" in window)){window.cmp_params=""}if(!("cmp_host" in window))'
    '{window.cmp_host="d.delivery.consentmanager.net"}if(!("cmp_cdn" in window)){window.cmp_cdn="cdn.consentmanager.net"}'
    'if(!("cmp_proto" in window)){window.cmp_proto="https:"}if(!("cmp_codesrc" in window)){window.cmp_codesrc="1"}'
    'window.cmp_getsupportedLangs=function(){var b=["DE","EN","FR","IT","NO","DA","FI","ES","PT","RO","BG","ET",'
    '"EL","GA","HR","LV","LT","MT","NL","PL","SV","SK","SL","CS","HU","RU","SR","ZH","TR","UK","AR","BS"]; '
    'if("cmp_customlanguages" in window){for(var a=0;a<window.cmp_customlanguages.length;a++)'
    "{b.push(window.cmp_customlanguages[a].l.toUpperCase())}}return b};window.cmp_getRTLLangs=function()"
    '{return["AR"]};window.cmp_getlang=function(j){if(typeof(j)!="boolean"){j=true}'
    'if(j&&typeof(cmp_getlang.usedlang)=="string"&&cmp_getlang.usedlang!=="")'
    "{return cmp_getlang.usedlang}var g=window.cmp_getsupportedLangs();var c=[];"
    'var f=location.hash;var e=location.search;var a="languages" in navigator?navigator.languages:[];if(f.indexOf("cmplang=")!=-1){c.push(f.substr(f.indexOf("cmplang=")+8,2).toUpperCase())}else{if(e.indexOf("cmplang=")!=-1)'
    '{c.push(e.substr(e.indexOf("cmplang=")+8,2).toUpperCase())}else{if("cmp_setlang" in window&&window.cmp_setlang!=""){c.push(window.cmp_setlang.toUpperCase())}else{if(a.length>0){for(var d=0;d<a.length;d++){c.push(a[d])}}}}}'
    'if("language" in navigator){c.push(navigator.language)}if("userLanguage" in navigator){c.push(navigator.userLanguage)}var h="";for(var d=0;d<c.length;d++){var b=c[d].toUpperCase();if(g.indexOf(b)!=-1){h=b;break}if(b.indexOf("-")!=-1){b=b.substr(0,2)}if(g.indexOf(b)!=-1){h=b;break}}'
    'if(h==""&&typeof(cmp_getlang.defaultlang)=="string"&&cmp_getlang.defaultlang!==""){return cmp_getlang.defaultlang}else{if(h==""){h="EN"}}h=h.toUpperCase();return h};(function(){var n=document;var p=window;var f="";var b="_en";if("cmp_getlang" in p){f=p.cmp_getlang().toLowerCase();'
    'if("cmp_customlanguages" in p){for(var h=0;h<p.cmp_customlanguages.length;h++){if(p.cmp_customlanguages[h].l.toUpperCase()==f.toUpperCase()){f="en";break}}}b="_"+f}function g(e,d){var l="";e+="=";var i=e.length;if(location.hash.indexOf(e)!=-1)'
    '{l=location.hash.substr(location.hash.indexOf(e)+i,9999)}else{if(location.search.indexOf(e)!=-1){l=location.search.substr(location.search.indexOf(e)+i,9999)}else{return d}}if(l.indexOf("&")!=-1){l=l.substr(0,l.indexOf("&"))}return l}var '
    'j=("cmp_proto" in p)?p.cmp_proto:"https:";var o=["cmp_id","cmp_params","cmp_host","cmp_cdn","cmp_proto"];for(var h=0;h<o.length;h++){if(g(o[h],"%%%")!="%%%"){window[o[h]]=g(o[h],"")}}var k=("cmp_ref" in p)?p.cmp_ref:location.href;'
    'var q=n.createElement("script");q.setAttribute("data-cmp-ab","1");var c=g("cmpdesign","");var a=g("cmpregulationkey","");q.src=j+"//"+p.cmp_host+"/delivery/cmp.php?"+("cmp_id" in p&&p.cmp_id>0?"id="+p.cmp_id:"")+("cmp_cdid" in p?"cdid="+p.cmp_cdid:"")+"&h="+encodeURIComponent(k)+(c!=""?"&cmpdesign="+encodeURIComponent(c):"")+(a!=""?"&cmpregulationkey="+'
    'encodeURIComponent(a):"")+("cmp_params" in p?"&"+p.cmp_params:"")+(n.cookie.length>0?"&__cmpfcc=1":"")+"&l="+f.toLowerCase()+"&o="+(new Date()).getTime();q.type="text/javascript";q.async=true;if(n.currentScript){n.currentScript.parentElement.appendChild(q)}else{if(n.body){n.body.appendChild(q)}else{var m=n.getElementsByTagName("body");if(m.length==0)'
    '{m=n.getElementsByTagName("div")}if(m.length==0){m=n.getElementsByTagName("span")}if(m.length==0){m=n.getElementsByTagName("ins")}if(m.length==0){m=n.getElementsByTagName("script")}if(m.length==0){m=n.getElementsByTagName("head")}if(m.length>0){m[0].appendChild(q)}}}var q=n.createElement("script");q.src=j+"//"+p.cmp_cdn+"/delivery/js/cmp"+b+".min.js";'
    'q.type="text/javascript";q.setAttribute("data-cmp-ab","1");q.async=true;if(n.currentScript){n.currentScript.parentElement.appendChild(q)}else{if(n.body){n.body.appendChild(q)}else{var m=n.getElementsByTagName("body");if(m.length==0){m=n.getElementsByTagName("div")}if(m.length==0){m=n.getElementsByTagName("span")}if(m.length==0)'
    '{m=n.getElementsByTagName("ins")}if(m.length==0){m=n.getElementsByTagName("script")}if(m.length==0){m=n.getElementsByTagName("head")}if(m.length>0){m[0].appendChild(q)}}}})();window.cmp_addFrame=function(b){if(!window.frames[b]){if(document.body){var a=document.createElement("iframe");a.style.cssText="display:none";a.name=b;document.body.appendChild(a)}'
    'else{window.setTimeout(window.cmp_addFrame,10,b)}}};window.cmp_rc=function(h){var b=document.cookie;var f="";var d=0;while(b!=""&&d<100){d++;while(b.substr(0,1)==" "){b=b.substr(1,b.length)}var g=b.substring(0,b.indexOf("="));if(b.indexOf(";")!=-1){var c=b.substring(b.indexOf("=")+1,b.indexOf(";"))}else{var c=b.substr(b.indexOf("=")+1,b.length)}if(h==g){f=c}'
    'var e=b.indexOf(";")+1;if(e==0){e=b.length}b=b.substring(e,b.length)}return(f)};window.cmp_stub=function(){var a=arguments;__cmapi.a=__cmapi.a||[];if(!a.length){return __cmapi.a}else{if(a[0]==="ping"){if(a[1]===2){a[2]({gdprApplies:gdprAppliesGlobally,cmpLoaded:false,cmpStatus:"stub",displayStatus:"hidden",apiVersion:"2.0",cmpId:31},true)}else{a[2](false,true)}}'
    'else{if(a[0]==="getUSPData"){a[2]({version:1,uspString:window.cmp_rc("")},true)}else{if(a[0]==="getTCData"){__cmapi.a.push([].slice.apply(a))}else{if(a[0]==="addEventListener"||a[0]==="removeEventListener"){__cmapi.a.push([].slice.apply(a))}else{if(a.length==4&&a[3]===false){a[2]({},false)}else{__cmapi.a.push([].slice.apply(a))}}}}}}};window.cmp_msghandler=function(d)'
    '{var a=typeof d.data==="string";try{var c=a?JSON.parse(d.data):d.data}catch(f){var c=null}if(typeof(c)==="object"&&c!==null&&"__cmpCall" in c){var b=c.__cmpCall;window.__cmp(b.command,b.parameter,function(h,g){var e={__cmpReturn:{returnValue:h,success:g,callId:b.callId}};d.source.postMessage(a?JSON.stringify(e):e,"*")})}if(typeof(c)==="object"&&c!==null&&"__cmapiCall" in c)'
    '{var b=c.__cmapiCall;window.__cmapi(b.command,b.parameter,function(h,g){var e={__cmapiReturn:{returnValue:h,success:g,callId:b.callId}};d.source.postMessage(a?JSON.stringify(e):e,"*")})}if(typeof(c)==="object"&&c!==null&&"__uspapiCall" in c){var b=c.__uspapiCall;window.__uspapi(b.command,b.version,function(h,g){var e={__uspapiReturn:{returnValue:h,success:g,callId:b.callId}}'
    ';d.source.postMessage(a?JSON.stringify(e):e,"*")})}if(typeof(c)==="object"&&c!==null&&"__tcfapiCall" in c){var b=c.__tcfapiCall;window.__tcfapi(b.command,b.version,function(h,g){var e={__tcfapiReturn:{returnValue:h,success:g,callId:b.callId}};d.source.postMessage(a?JSON.stringify(e):e,"*")},b.parameter)}};window.cmp_setStub=function(a){if(!(a in window)||'
    '(typeof(window[a])!=="function"&&typeof(window[a])!=="object"&&(typeof(window[a])==="undefined"||window[a]!==null))){window[a]=window.cmp_stub;window[a].msgHandler=window.cmp_msghandler;window.addEventListener("message",window.cmp_msghandler,false)}};window.cmp_addFrame("__cmapiLocator");window.cmp_addFrame("__cmpLocator");window.cmp_addFrame("__uspapiLocator");'
    'window.cmp_addFrame("__tcfapiLocator");window.cmp_setStub("__cmapi");window.cmp_setStub("__cmp");window.cmp_setStub("__tcfapi");window.cmp_setStub("__uspapi");',
    # consentmanager.net
    "d\.delivery\.consentmanager\.net",  # consentmanager.net
    "https://cdn\.consentmanager\.net/delivery/autoblocking/3834f5ec2941\.js",  # consentmanager.net
    "https://cdn\.jsdelivr\.net/npm/cookie-bar/cookiebar-latest.min\.js",  # cookieBAR
    '<a href="#" onclick="document\.cookie=\'cookiebar=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/\'; setupCookieBar\(\); return false;">Click here to revoke the Cookie consent</a>',
    # cookieBAR
    "(https:\/\/|http:\/\/)?consent\.cookiebot\.com\/.*\.js",  # Cookiebot
    "((cdn\.jsdelivr\.net).*|window\.)cookieconsent(\.js|\.css|\.min\.js|\.min\.css|\.initialise)",
    # Cookie Consent
    # 'https://cdn.jsdelivr.net/npm/cookieconsent@3/build/cookieconsent.min.css', # Cookie Consent
    # 'https://cdn.jsdelivr.net/npm/cookieconsent@3/build/cookieconsent.min.js', # Cookie Consent
    # 'window.cookieconsent.initialise', # Cookie Consent
    "https://policy\.app\.cookieinformation\.com/uc\.js",  # Cookie Information
    "(https:|http:)?//cdn.cookie-script.com/.*.js",  # Cookie Script
    "(jquery\.|\.)?cookieBar(\.js|\.css)?",  # jquery.cookieBar
    "jquery-eu-cookie-law-popup(\.js|\.css)",  # jQuery EU Cookie Law popups
    "user_cookie_already_accepted|user_cookie_consent_changed",  # jQuery EU Cookie Law popups (events regex)
    "otBannerSdk(\.js)?|(ot|onetrust)-banner(-sdk)?|(window\.)?OneTrust(\.LoadBanner)?",  # OneTrust
    "Quantcast|window\._qevents|pixel\.quantserve\.com(\/pixel)?",  # Quantcast Choice
    "truste-consent-button|truste-consent-required|truste-show-consent|consent\.trustarc\.com",  # TrustArc (TRUSTe)
    "cookie(-|_)bar(-js|-css|\.css|\.js)|cookie_bar_message|cookie_bar_button|cookie_bar_btn_bg_colour",  # Cookie Bar (WordPress Plugins)
    "",  # Cookie Consent (TODO:)
    "cookie-law-bar-setting|cookie-law-bar(\.js|-js|-css|\.css)",  # Cookie Law Bar
    "settings_page_cookie-notice|cookie-notice-admin|cookie-notice-front|cookie_notice_options|cookie_notice_version|cookie_notice_accepted|cn_is_cookie_accepted|reset_cookie_notice_options|cookie-notice",  # Cookie Notice for GDPR
    "custom(-|_)cookie(-|_)message(-popup\.css|-popup-styles|-popup\.js)?|custom-cookie-message-popup\.js|custom-cookie-message-popup\.css|custom-cookie-message-popup-styles",  # Custom Cookie Message
    'eu_cookie_law_frontend_popup|eu_cookie_law_frontend_banner|eucookielaw-scripts|class="eucookie"|eu-cookie-law|<div class="pea_cook_more_info_popover"><div class="pea_cook_more_info_popover_inner"',  # EU Cookie Law
    '<span role="link" tabindex="0" data-href="#moove_gdpr_cookie_modal" class="change-settings-button">|moove-gdpr-info-bar-hidden|moove-gdpr-align-center|gdpr-cookie-compliance',  # GDPR Cookie Compliance
    "",  # GDPR Cookie Consent (TODO:)
    "options-general\.php?page=gdpr-tools-setting|jquery\.eu-cookie-consent\.js|gdpr-tools-public\.js|gdpr-tools-public\.css|gdpr-tools-data-settings|gdpr-confirm-wrapper",  # GDPR Tools
    "",  # WF Cookie Consent (TODO:)
    "",  # Cookie Control (Drupal Modules) (TODO:)
    "",  # EU Cookie Compliance (TODO:)
    "",  # Simple Cookie Compliance (TODO:)
    "evidon-banner\.js",  # Crownpeak (Evidon)
    "evidon.*.js",  # Crownpeak (Evidon)
    "didomi",  # Didomi
]

banner_patterns = [
    "gebruik van.*cookies",
    "accept.*cookie",
    "decline cookie",
    "reject cookie",
    "reject all cookies",
    "cookie consent",
    "accept all cookies",
    "cookie settings",
    "I agree",
    "I accept",
    "allow all cookies",
    "use of cookies",
    "Ik ga akkoord",
    "cookies accepteren",
    "cookievoorkeuren",
    "noodzakelijke cookies",
    "functionele cookies",
    "alles accepteren",
    "accept all",
    "alle cookies accepteren",
    "cookie instellingen",
    "OneTrust-Consent",
    "Civic Cookie Control",
    "Clickio Consent Tool",
    "consentmanager.net",
    "cookieBAR",
    "Cookiebot",
    "Cookie Consent",
    "Cookie Information",
    "Crownpeak (Evidon)",
    "Didomi",
    "jquery.cookieBar",
    "jQuery EU Cookie Law popups",
    "OneTrust",
    "Quantcast Choice",
    "TrustArc",
]

languages = ["fr", "es", "hi"]


# Translate the given word to the given language. The language should be in abbreviation form, e.g 'nl' or 'de'.
def translate(word, lang):
    return GoogleTranslator(source="auto", target=lang).translate(word)


for lang in languages:
    external_patterns = map(lambda x: translate(x, lang), banner_patterns)
    banner_patterns.extend(external_patterns)
