from deep_translator import GoogleTranslator

lib_js_file_names = [
    "https://cc\.cdn\.civiccomputing\.com/.*(\.min\.js|\.js)",  # Civic Cookie Control
    # "https://cc\.cdn\.civiccomputing\.com/9/cookieControl-9\.x\.min\.js",  # Civic Cookie Control
    # "https://cc\.cdn\.civiccomputing\.com/9/cookieControl-9\.5\.min\.js",
    # "clickio\.mgr\.consensu\.org/t/consent_225761\.js",  # Clickio Consent Tool
    "clickio\.mgr\.consensu\.org\/.*\.js",  # Clickio Consent Tool
    '{window\.cmp_host="d\.delivery\.consentmanager\.net"}if\(!\("cmp_cdn" in window\)\){window\.cmp_cdn="cdn\.consentmanager\.net"}|var q=n\.createElement\("script"\);q\.setAttribute\("data-cmp-ab","1"\);var c=g\("cmpdesign",""\);var a=g\("cmpregulationkey",""\);q\.src=j\+"\/\/"\+p\.cmp_host\+"\/delivery\/cmp\.php\?"\+\("cmp_id" in p&&p\.cmp_id>0\?"id="\+p\.cmp_id:""\)\+\("cmp_cdid" in p\?"cdid="\+p\.cmp_cdid:""\)\+"&h="\+encodeURIComponent\(k\)\+\(c!=""\?"&cmpdesign="\+encodeURIComponent\(c\):""\)\+\(a!=""\?"&cmpregulationkey="\+',
    # consentmanager.net
    "d\.delivery\.consentmanager\.net",  # consentmanager.net
    "https://cdn\.consentmanager\.net/delivery/autoblocking/3834f5ec2941\.js",  # consentmanager.net
    "https://cdn\.jsdelivr\.net/npm/cookie-bar/cookiebar-latest.min\.js",  # cookieBAR
    '<a href="#" onclick="document\.cookie=\'cookiebar=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/\'; setupCookieBar\(\); return false;">Click here to revoke the Cookie consent</a>',
    # cookieBAR
    "(https:\/\/|http:\/\/)?consent\.cookiebot\.com\/.*\.js",  # Cookiebot
    "((cdn\.jsdelivr\.net).*|window\.)cookieconsent(\.js|\.css|\.min\.js|\.min\.css|\.initialise)",  # Cookie Consent
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
    "cookiechoices\.min\.js|page=wf-cookieconsent|wf_cookieconsent_options_page|wf-cookieconsent|wf_cookieconsent_setting_textarea|wf-cookie-consent|wf_cookieconsent_options",  # WF Cookie Consent
    "cookieControl-.*\.js|CookieControl\.cookieLawApplies\(|CookieControl\.consented\(|CookieControl\.maySendCookies\(",  # Cookie Control (Drupal Modules)
    '\.removeClass\("cctoggle-text-on"\)\.addClass\("cctoggle-text-off"\);jQuery\("#cctoggle-text"\)\.html\(CookieControl\.options\.cookieOffText\);if\(CookieControl\.options\.consentModel=="implicit"\){jQuery\("#cccwr #ccc-implicit-warning"\)\.show\(\)}else{if\(CookieControl\.options\.consentModel=="explicit"\){jQuery\("#cccwr #ccc-explicit-checkbox"\)\.show\(\)}}}}}else{if\(d==false\){c\.removeClass\("ccc-pause"\)\.addClass\("ccc-go"\);jQuery\("#cctoggle-text"\)\.removeClass\("cctoggle-text-off"\)\.addClass\("cctoggle-text-on"\);',
    "Drupal\.eu_cookie_compliance\(|Drupal\.eu_cookie_compliance\.queue|Drupal\.eu_cookie_compliance|eu_cookie_compliance_category_overview_form|eu_cookie_compliance\.js|eu-cookie-compliance-check|eu-cookie-compliance-status-|eu-cookie-compliance-banner|eu-cookie-compliance-popup-open|eu-cookie-compliance-categories|eu-cookie-compliance/store_consent/banner",  # EU Cookie Compliance
    'js-cookie-compliance__agree|simple_cookie_compliance\.js|simple_cookie_compliance\.css|class="cookie-compliance__button js-cookie-compliance__agree"|<div class="cookie-compliance__inner">|<div class="cookie-compliance__text">',  # Simple Cookie Compliance
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
