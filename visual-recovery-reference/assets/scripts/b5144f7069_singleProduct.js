(function($){
$(document).ready(function() {
    
$('.woocommerce div.product form.cart table.variations tr label[for="pa_color"]').after(`

<div class="select-color-wrap">
  <a href="/product-category/red/" class="select-color">
    <i class="fa fa-plus"></i>
    <span>Select a Color</span>
   </a>
</div>
`);        
    
    
});  	
})(jQuery);