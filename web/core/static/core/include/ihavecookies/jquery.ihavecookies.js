/*!
 * ihavecookies - jQuery plugin for displaying cookie/privacy message
 * v0.3.2
 *
 * Copyright (c) 2018 Ketan Mistry (https://iamketan.com.au)
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/mit-license.php
 *
 */
/*!
 * ihavecookies - jQuery plugin for displaying cookie/privacy message
 * v0.3.2
 *
 * Copyright (c) 2018 Ketan Mistry (https://iamketan.com.au)
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/mit-license.php
 *
 */
/*
 * Michael Perk - Added the option which disables the advanced buttons for technical cookies only.
 */
!function(e){e.fn.ihavecookies=function(n,c){var r=e(this),a=e.extend({cookieTypes:[{type:"Site Preferences",value:"preferences",description:"These are cookies that are related to your site preferences, e.g. remembering your username, site colours, etc."},{type:"Analytics",value:"analytics",description:"Cookies related to site visits, browser types, etc."},{type:"Marketing",value:"marketing",description:"Cookies related to marketing, e.g. newsletters, social media, etc"}],title:"Cookies & Privacy",message:"Cookies enable you to use shopping carts and to personalize your experience on our sites, tell us which parts of our websites people have visited, help us measure the effectiveness of ads and web searches, and give us insights into user behavior so we can improve our communications and products.",link:"/privacy-policy",delay:2e3,expires:30,moreInfoLabel:"More information",acceptBtnLabel:"Accept Cookies",advancedBtnLabel:"Customise Cookies",cookieTypesTitle:"Select cookies to accept",fixedCookieTypeLabel:"Necessary",fixedCookieTypeDesc:"These are cookies that are essential for the website to work correctly.",onAccept:function(){},uncheckBoxes:!1,hasAdvancedCookies:!0},n),s=t("cookieControl"),p=t("cookieControlPrefs");if(s&&p&&"reinit"!=c){var d=!0;"false"==s&&(d=!1),o(d,a.expires)}else{e("#gdpr-cookie-message").remove();var l='<li><input type="checkbox" name="gdpr[]" value="necessary" checked="checked" disabled="disabled"> <label title="'+a.fixedCookieTypeDesc+'">'+a.fixedCookieTypeLabel+"</label></li>";preferences=JSON.parse(p),e.each(a.cookieTypes,function(e,o){if(""!==o.type&&""!==o.value){var i="";!1!==o.description&&(i=' title="'+o.description+'"'),l+='<li><input type="checkbox" id="gdpr-cookietype-'+o.value+'" name="gdpr[]" value="'+o.value+'" data-auto="on"> <label for="gdpr-cookietype-'+o.value+'"'+i+">"+o.type+"</label></li>"}});var u="",k="";a.hasAdvancedCookies&&(u='<button id="gdpr-cookie-advanced" type="button">'+a.advancedBtnLabel+"</button>",k="<ul>"+l+"</ul>");var f='<div id="gdpr-cookie-message"><h4>'+a.title+"</h4><p>"+a.message+' <a href="'+a.link+'">'+a.moreInfoLabel+'</a><div id="gdpr-cookie-types" style="display:none;"><h5>'+a.cookieTypesTitle+"</h5>"+k+'</div><p><button id="gdpr-cookie-accept" type="button">'+a.acceptBtnLabel+"</button>"+u+"</p></div>";setTimeout(function(){e(r).append(f),e("#gdpr-cookie-message").hide().fadeIn("slow",function(){"reinit"==c&&(e("#gdpr-cookie-advanced").trigger("click"),e.each(preferences,function(o,i){e("input#gdpr-cookietype-"+i).prop("checked",!0)}))})},a.delay),e("body").on("click","#gdpr-cookie-accept",function(){o(!0,a.expires),e('input[name="gdpr[]"][data-auto="on"]').prop("checked",!0);var t=[];e.each(e('input[name="gdpr[]"]').serializeArray(),function(e,o){t.push(o.value)}),i("cookieControlPrefs",encodeURIComponent(JSON.stringify(t)),365),a.onAccept.call(this)}),e("body").on("click","#gdpr-cookie-advanced",function(){e('input[name="gdpr[]"]:not(:disabled)').attr("data-auto","off").prop("checked",!1),e("#gdpr-cookie-types").slideDown("fast",function(){e("#gdpr-cookie-advanced").prop("disabled",!0)})})}!0===a.uncheckBoxes&&e('input[type="checkbox"].ihavecookies').prop("checked",!1)},e.fn.ihavecookies.cookie=function(){var e=t("cookieControlPrefs");return JSON.parse(e)},e.fn.ihavecookies.preference=function(e){var o=t("cookieControl"),i=t("cookieControlPrefs");return i=JSON.parse(i),!1!==o&&(!1!==i&&-1!==i.indexOf(e))};var o=function(o,t){i("cookieControl",o,t),e("#gdpr-cookie-message").fadeOut("fast",function(){e(this).remove()})},i=function(e,o,i){var n=new Date;n.setTime(n.getTime()+24*i*60*60*1e3);var c="expires="+n.toUTCString();return document.cookie=e+"="+o+";"+c+";path=/",t(e)},t=function(e){for(var o=e+"=",i=decodeURIComponent(document.cookie).split(";"),t=0;t<i.length;t++){for(var n=i[t];" "==n.charAt(0);)n=n.substring(1);if(0===n.indexOf(o))return n.substring(o.length,n.length)}return!1}}(jQuery);