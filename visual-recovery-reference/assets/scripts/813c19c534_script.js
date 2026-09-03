(function($){
$(document).ready(function() {

change_webfont();

$("#surface").select2({
    tags: true,
    tokenSeparators: [',', ' ']
})  
		
$('#location,#finish,.tabs_selects_wrap select').niceSelect();
function get_term_colors(options){
    colorResultsWrap = $('.color_results_item');
	$('.color_result_side_box_wrap').hide();
	$.ajax({
		url : window.location.origin+themesky_params.ajax_uri,
		type:'post',
		beforeSend:function(){
		  $('.color_results_item_wrap').hide();
		  $('#color_preloader').show();
		},
		data: {
		  action:'get_term_colors',
		  fields : options
	    },
		success:function(response){	
// 		  console.log(response);
		  let htmlData = "";
		  let wishlist = ""; 
		  if(response.success && response.data.result){
		  response.data.result.forEach((item) => {
		  if(item){
		     htmlData += `<div class="color_result_box" style="background-color:${item.color}"> <a href="javascript:0;" data-color="${item.color}" data-term-slug="${item.term_slug}" data-term-link="${item.term_link}" data-term="${item.term_id}"><span>${item.term_name}</span></a><i class="${item.wishlist ? "fas" : "far"} fa-heart add_to_wish_list" onclick="addToWishList(${item.term_id},event)" data-term-id="${item.term_id}"></i></div>`;    
		  }});
		   $('#color-cat-name h3').text(response.data.tax_data.tax_name);
		   $('.color_results_item_wrap').attr('data-term-wrap',response.data.tax_data.tax_id);
		     colorResultsWrap.html(htmlData); 
		   }
		   else{
		    colorResultsWrap.html(`<h3>No Colors Found.</h3>`);   
		   }
		   setTimeout(() => {
		   $('#color_preloader').hide();
		   $('.color_results_item_wrap').show();
		   },400)		    
		}
	})
}	
	
  $('#color_options_wrap .color_option').on('click',function(){
	  let $this = $(this);
	  let termId = $this.data('term-id');
	  let termName = $this.data('color-name');
	  let terms = $this.data('terms');
	  $this.siblings().removeClass('active');
	  $this.addClass('active');
	  let location = $('#location-field .nice-select .selected').data('value');
	  let surface = $('#surface-field #surface').val();
	  let finish = $('#finish-field .nice-select .selected').data('value');
	  let term_fields = {
		  termId,
		  termName,
		  terms,
		  location,
		  surface,
		  finish
	  }
	  get_term_colors(term_fields);
	  $('[data-term-wrap]').removeClass('active');
	  let colorWrapper = $('[data-term-wrap="'+termId+'"]');
	  colorWrapper.show().addClass('active').siblings().hide();
  });
	
});

// $('a').not('#menu-1-d5998eb li a,.logo a,footer a').attr('href','javascript:0;');
	
$('.colorselection_field').on('change','select',function(){
    $(this).niceSelect('update');
    $('#color_options_wrap .color_option.active').trigger('click');
});

$(document).on('click','.color_result_box a',function(){
  $('.color_result_side_box_wrap').slideUp();
  let termId = $(this).data('term');
  let termSlug = $(this).data('term-link');
  $('body').append('<div id="background-layer"></div>')
  let termColor = $(this).data('color');
  var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?attribute_pa_color='+termId;
  window.history.pushState({ path: newurl }, '', newurl);  
  let colorName = $(this).text();
  $('.color_result_side_box_wrap').slideDown();
  $('.add_to_wish_list').attr('onclick', 'addToWishList('+termId+',event)');
   $('#color_result_side_box_label').html(`<span>${colorName}</span>`);
   $('#add_to_wish_list').attr('data-term-id', termId);
   $('#color_archive_action').attr('href',termSlug);
   $('.color_result_side_box_color_box').css('background-color',termColor); 
})
$('#color_result_side-box_cross').click(function(){
	 $('.color_result_side_box_wrap').slideUp();
	 $('body #background-layer').hide();
});		

$('.product-group-button').each((index,item) => {
	let productId = jQuery(item).closest('.product').data('product_id');
	jQuery(item).prepend(
	`<div class="button-in wishlist">
 <div class="product-wishlist-wrap">
	<span class="feedback"><i class="yith-wcwl-icon fa fa-heart"></i></span>
	  <a href="javascript:0;" rel="nofollow" data-title="Browse wishlist" onclick="addProductToWishlist(${productId},event)">
		<span class="ts-tooltip button-tooltip" data-title="Add to wishlist">Wishlist</span>	
	  </a>
   </div>
</div>`) });	
	
	
$('aside.filter-widget-area .widget-title.heading-title').click(function(){
	let $this = $(this);
	$this.toggleClass('active');
	$this.closest('.widget-title-wrapper').next().slideToggle(300);
})	
	
$('.tabs_buttons_wrap .term-link').click(function(){
	let $this = jQuery(this);
	let termId = $this.data('term');
	$this.parent().addClass('active').siblings().removeClass('active');
	$('.inspiration_posts_wrap-tabs[data-tab]').removeClass('active').hide();
	$('.inspiration_posts_wrap-tabs[data-tab="'+termId+'"]').addClass('active').fadeIn();
});
	
$(document).on('click','.inspiration-wishlist',function(){
    let $this = $(this);
    let postID = $this.data('term-id');
    let loggedIn = jQuery('body').hasClass('logged-in');
	if(postID && loggedIn){
  	$.ajax({
	  type:"post",
	  url:window.location.origin+themesky_params.ajax_uri,
	  data: {
		  action:'inspiration_wishlist',
		  post_id : postID
	    },
	  success:function(response){
	      if(response.data.added){
	         $('[data-term-id ="'+postID+'"] .fa-heart').addClass('fas').removeClass('far');
			 Snackbar.show({ text: response.data.message, pos: 'bottom-left' });
			 //jQuery('.count-number').text(response.data.count);
		  }else{
		     $('[data-term-id ="'+postID+'"] .fa-heart').addClass('far').removeClass('fas');
			 Snackbar.show({ text: response.data.message, pos: 'bottom-left' });
		  }
	   //   console.log(response);
	   }
  	});
	}else{
	    Snackbar.show({ text: 'You should login first.<a href="/my-account/">Click here to login</a>', pos: 'bottom-left' }) 
	}
});
	
$('.inspiration_filter_form').on('change',function(e){
    e.preventDefault();
    let $this = $(this);
	let formData = $this.serialize();
	let termId = $('.tabs_buttons_wrap .active .term-link').data('term');
	$('.inspiration-loader').show();
	$('.inspiration-main-tab').hide();
	let html = '';
	$.ajax({
	  type:"post",
	  url:window.location.origin+themesky_params.ajax_uri,
	  data: {
		  action:'inspiration_filter',
		  formData : formData
	    },
		success:function(response){
// 		 console.log(response);
		 
		  if(response.success){
			 response.data.posts.forEach((item,index) => {
				 let $colors = '';
				 item.colors.forEach((color) => {
					 $colors += `<div class='color_box' style='background-color:${color.name}'><span>${color.code}</span></div>`;
				 }); 
				 html += `<div class="inspiration_posts_item">
				  <div class="inspiration-wishlist" data-term-id="${item.ID}">
				    <i class="${item.className} fa-heart add_to_wish_list"></i>
				  </div>
				  <a data-fancybox="demo" data-src="${item.thumbnail}" data-caption="<div class='inspiration_color_boxes'>${$colors}</div>">
                    <img src="${item.thumbnail}" loading="lazy" alt="${item.post_title}">                    
                  </a>
				 <div class="inspiration_color_boxes">${$colors}</div></div>`;
			 });
			   $('[data-tab="'+termId+'"] .inspiration_posts_wrap').html(html); 
		     }else{
			  $('[data-tab="'+termId+'"] .inspiration_posts_wrap').html(response.data.message);
		     }
    		     if(response.data.filter){
        			  $('[data-tab="'+termId+'"] .clear_inspiration_filter').show();
        			}else{
        			  $('[data-tab="'+termId+'"] .clear_inspiration_filter').hide();
        	 }
			$('.inspiration-loader').hide();
			$('.inspiration-main-tab').show();
		 }
	});
});

$('.inspiration_filter_form').on('submit',function(e){
    e.preventDefault();
    let form = $(this);
    let termId = $('.tabs_buttons_wrap .active .term-link').data('term');
    let emptyForm = $('[data-tab="'+termId+'"] .inspiration_filter_form select');
    let checkEmpty = false;
    emptyForm.each((index,item)=>{
        if($(item).val() != null){
          checkEmpty = true;
        }
    });
    
    if(checkEmpty){
      form[0].reset();
      form.trigger('change');
      form[0].reset();
    }else
    {
     Snackbar.show({ text: "Fields Sholud be Selected", pos: 'top-right' });     
    }
    
});

$(document).on("mouseover",'#color_options_wrap .add_to_wish_list,.color_result_side_box_color_box .add_to_wish_list i', function () {
    if($(this).hasClass('far')){
       $(this).removeClass('far').addClass('fas heart-active');
    }
});

$(document).on("mouseleave",'#color_options_wrap .add_to_wish_list,.color_result_side_box_color_box .add_to_wish_list i', function () {
    if($(this).hasClass('heart-active')){
      $(this).addClass('far').removeClass('fas heart-active');
    }
});

$(document).on('click','.inspiration_posts_wrap-tabs .loadmore_tigger', function(){
		var button = $(this),
		    html='',
		    termId = button.data('cat'),
		    pageNumber = button.attr('data-page'),
		    data = {
			'action': 'loadmore',
			'pageNumber' : parseInt(pageNumber),
			'ppp' : 9,
			'cat' : termId,
		};
        console.log(parseInt(pageNumber));
		$.ajax({ // you can also use $.post here
			url : emirates_params.ajaxurl, // AJAX handler
			data : data,
			type : 'POST',
			beforeSend : function ( xhr ) {
				button.text('Loading...'); // change the button text, you can also add a preloader image
			},
			success : function( data ){
				if( data.success &&  data.data.posts != null) {
				    data.data.posts.forEach((item,index) => {
    				 let $colors = '';
    				 item.colors.forEach((color) => {
    					 $colors += `<div class='color_box' style='background-color:${color.name}'><span>${color.code}</span></div>`;
    				 }); 
    				 html += `<div class="inspiration_posts_item">
    				  <div class="inspiration-wishlist" data-term-id="${item.ID}">
    				    <i class="${item.className} fa-heart add_to_wish_list"></i>
    				  </div>
    				  <a data-fancybox="demo" data-src="${item.thumbnail}" data-caption="<div class='inspiration_color_boxes'>${$colors}</div>">
                        <img src="${item.thumbnail}" width="402" height="423" loading="lazy" alt="${item.post_title}">                    
                      </a>
    				 <div class="inspiration_color_boxes">${$colors}</div></div>`;
        			 });
    			   $('[data-tab="'+termId+'"] .inspiration_posts_wrap').append(html);
				    ++pageNumber;
				    button.attr('data-page',pageNumber);
					button.text( 'More Inspirations' ).prev().before(data); // insert new posts
					emirates_params.current_page++;
 
					if ( emirates_params.current_page == emirates_params.max_page ) 
						button.remove(); // if last page, remove the button
 
					// you can also fire the "post-load" event here if you use a plugin that requires it
					// $( document.body ).trigger( 'post-load' );
				} else {
					button.remove();
				    $('[data-tab="'+termId+'"]').append('<span class="no-inspirations">No More Inspirations</span>');
				}
			}
		});
	});

	
})(jQuery);

jQuery(window).on('load',function(){
  var currentTermId = jQuery('#current_term_id').val();
  jQuery('.color_options [data-term-id="'+currentTermId+'"]').trigger('click');	  
})

function countTotalWishlistItems()
{
  let totalCount = jQuery('#colors_list table tr,#inspiration_list table tr,#products_list table tr').not('.table__head').length;    
  return totalCount;
}


function removeFormWishList(termid,event){
	let termId = termid;
	let $this = jQuery(event.target);
	if(termId){
	jQuery.ajax({
		url:window.location.origin+themesky_params.ajax_uri,
		type:'post',
		beforeSend:function(){
		  $this.parent().html('<span class="spinner"></span>');
		},
		data: {
		  action:'custom_remove_from_wishlist',
		  term_id : termId
	    },
		success:function(response){
// 		console.log(response);
		  if(response.success){
			 jQuery('.spinner').remove();
			 jQuery('.wishlist_colors_wrap [data-term="'+termId+'"]').remove();
			 jQuery('.color_count').text(response.data.count);
			 if(response.data.count == 0){
		        jQuery('#colors_list').closest('.color_wishlist_wrap').remove();
		     }
			 if(countTotalWishlistItems() == 0){
		      jQuery('.empty__wishlist').show();    
		    }
		  }else{
			  Snackbar.show({ text: response.data.message, pos: 'top-right' }); 
		  }
		}
	});	
}}

function addToWishList(termid,event){
	let termId = termid;
	let $this = jQuery(event.target);
	let loggedIn = jQuery('body').hasClass('logged-in');
	if(termId && loggedIn){
	jQuery.ajax({
		url:window.location.origin+themesky_params.ajax_uri,
		type:'post',
		beforeSend:function(){
		},
		data: {
		  action:'custom_add_to_wishlist',
		  term_id : termId
	    },
		success:function(response){
		  if(response.data.added){
			   $this.addClass('fas').removeClass('far'); 
		       Snackbar.show({ text: response.data.message, pos: 'bottom-left' });
		  }else{
		     $this.addClass('far').removeClass('fas'); 
			 Snackbar.show({ text: response.data.message, pos: 'bottom-left' });
		  }
		}
	});
 }else{
	 Snackbar.show({ text: 'You should login first.<a href="/my-account/">Click here to login</a>', pos: 'bottom-left' });
 }
}	

function addProductToWishlist(postId,event){
	let postID = postId;
	let $this = jQuery(event.target);
	let isSingle = jQuery('body').hasClass('single-product');
// 	alert(postID);
	let loggedIn = jQuery('body').hasClass('logged-in');
	if(loggedIn){
	jQuery.ajax({
		url:window.location.origin+themesky_params.ajax_uri,
		type:'post',
		beforeSend:function(){
		},
		data: {
		  action:'custom_add_product_to_wishlist',
		  post_id : postID
	    },
		success:function(response){
		if(isSingle){
		  if(response.data.added){
		    $this.find('i').addClass('fas').removeClass('far');
		  }else{
		    $this.find('i').addClass('far').removeClass('fas');
		    Snackbar.show({ text: response.data.message, pos: 'bottom-left' }); 
		}
		}else{
		  if(response.data.added){
		      $this.closest('.wishlist').addClass('active');
		      Snackbar.show({ text: response.data.message, pos: 'bottom-left' }); 
    	   }else
    	   {
    		  $this.closest('.wishlist').removeClass('active');
    		  Snackbar.show({ text: response.data.message, pos: 'bottom-left' }); 
    	   }
    	  }
		}
		
	});
 }else{
	 Snackbar.show({ text: 'You should login first.<a href="/my-account/">Click here to login</a>', pos: 'bottom-left' });
 }
}	

function removeProductFormWishList(postId,event){
	let postID = postId;
	let $this = jQuery(event.target);
// 	alert(postID);
	let loggedIn = jQuery('body').hasClass('logged-in');
	if(loggedIn){
	jQuery.ajax({
		url:window.location.origin+themesky_params.ajax_uri,
		type:'post',
		beforeSend:function(){
	     $this.parent().html('<span class="spinner"></span>');
	    },
		data: {
		  action:'custom_remove_product_from_wishlist',
		  post_id : postID
	    },
		success:function(response){
// 		console.log(response);
		  if(response.success){
			jQuery('#products_list [data-product-id="'+postID+'"]').remove();	
		    jQuery('.products_count').text(response.data.count);
		    if(response.data.count == 0){
		      jQuery('#products_list').closest('.color_wishlist_wrap').remove();
		    }
		    if(countTotalWishlistItems() == 0){
		      jQuery('.empty__wishlist').show();   
		    }
		  }else{
		   Snackbar.show({ text: response.data.message, pos: 'top-right' });
// 			console.log(response.data.message);
		  }
		}
	});
 }else{
	 Snackbar.show({ text: 'You should login first.<a href="/my-account/">Click here to login</a>', pos: 'top-right' });
 }
}


function removeInspirationFormWishList(postId,event){
	let postID = postId;
	let $this = jQuery(event.target);
	let loggedIn = jQuery('body').hasClass('logged-in');
	if(loggedIn){
	jQuery.ajax({
		url:window.location.origin+themesky_params.ajax_uri,
		type:'post',
		beforeSend:function(){
	     $this.parent().html('<span class="spinner"></span>');
	    },
		data: {
		  action:'custom_remove_inspiration_from_wishlist',
		  post_id : postID
	    },
		success:function(response){
// 		console.log(response);
		  if(response.success){
			jQuery('#inspiration_list [data-inspiration-id="'+postID+'"]').remove();	
		    jQuery('.products_count').text(response.data.count);
		    if(response.data.count == 0){
		        jQuery('#inspiration_list').closest('.color_wishlist_wrap').remove();
		    }
		    if(countTotalWishlistItems() == 0){
		      jQuery('.empty__wishlist').show();    
		    }
		  }else{
		       Snackbar.show({ text: response.data.message, pos: 'top-right' });
// 			console.log(response.data.message);
		  }
		}
	});
 }else{
	 Snackbar.show({ text: 'You should login first.<a href="/my-account/">Click here to login</a>', pos: 'top-right' });
 }
}

jQuery("[data-fancybox]").fancybox({
  thumbs          : false,
  hash            : false,
  loop            : true,
  keyboard        : true,
  toolbar         : false,
  animationEffect : false,
  arrows          : true,
  clickContent: 'close',
  buttons: ['close']
});


// 	change Arbic Font

// jQuery(document).on('click', '.g_translate_box a', function(){
// 	change_webfont();
// });


function change_webfont(){
jQuery('*').each(function(index, item){
    if(jQuery(this).css('font-family') == 'Jost' || jQuery(this).css('font-family') == 'Raleway' || jQuery(this).css('font-family') == 'Metropolis' || jQuery(this).css('font-family') == 'arial' || jQuery(this).css('font-family') == 'Metrophobic, sans-serif' || jQuery(this).css('font-family') == 'Raleway, sans-serif'){
        jQuery(this).attr('data-eng-ff', jQuery(this).css('font-family'));
        //jQuery(this).attr('data-ar-ff', 'Dubai');
        //jQuery(this).css({'font-family': 'Dubai', 'letter-spacing': '0'});
    }   
});
}

// 	change Arbic Font