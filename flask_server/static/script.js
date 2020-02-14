'use strict';

function waitForDOM(callback){
    const domReady = (/in/.test(document.readyState));

    // if DOM is not ready, put the callback on the event stack
    (domReady) ? setTimeout('waitForDOM('+callback+')', 9) : callback()
}

function setupEventListeners(){
    if (!document.getElementsByClassName) {
        // IE8 support
        var getElementsByClassName = function(node, classname) {
            var a = [];
            var re = new RegExp('(^| )'+classname+'( |$)');
            var els = node.getElementsByTagName("*");
            for(var i=0,j=els.length; i<j; i++)
                if(re.test(els[i].className))a.push(els[i]);
            return a;
        }
        var videos = getElementsByClassName(document.body,"video");
    } else {
        var videos = document.getElementsByClassName("video");
    }

    var nb_videos = videos.length;
    for (var i=0; i<nb_videos; i++) {

        videos[i].style.backgroundImage = 'url(https://img.youtube.com/vi/' + videos[i].id + '/3.jpg)';

        videos[i].onclick = function() {
            var iframe = document.createElement("iframe");
            var iframe_url = "https://www.youtube-nocookie.com/embed/" + this.id;
            
            iframe.setAttribute("src",iframe_url);
            iframe.setAttribute("frameborder",'0');
            iframe.setAttribute('allowFullScreen', '')

            this.parentNode.replaceChild(iframe, this);
        }
    }

    var hideButtons = document.getElementsByClassName("hide");

    for (var j = 0; j < hideButtons.length; j++){
        hideButtons[j].addEventListener("click", function(){
            this.parentNode.parentNode.className = "hidden";
        });
    }
}

waitForDOM(setupEventListeners);

(function() {
    var stripe = Stripe('pk_test_gzyt6jbnmoUbgNoKu6zFPHZn00P6Re50lj');
  
    var checkoutButton = document.getElementById('checkout-button-sku_GjNmfTwM80vRpw');
    checkoutButton.addEventListener('click', function () {
      // When the customer clicks on the button, redirect
      // them to Checkout.
      stripe.redirectToCheckout({
        items: [{sku: 'sku_GjNmfTwM80vRpw', quantity: 1}],
  
        // Do not rely on the redirect to the successUrl for fulfilling
        // purchases, customers may not always reach the success_url after
        // a successful payment.
        // Instead use one of the strategies described in
        // https://stripe.com/docs/payments/checkout/fulfillment
        successUrl: 'https://really-good-music-videos.herokuapp.com/success',
        cancelUrl: 'https://really-good-music-videos.herokuapp.com',
      })
      .then(function (result) {
        if (result.error) {
          // If `redirectToCheckout` fails due to a browser or network
          // error, display the localized error message to your customer.
          var displayError = document.getElementById('error-message');
          displayError.textContent = result.error.message;
        }
      });
    });
  })();