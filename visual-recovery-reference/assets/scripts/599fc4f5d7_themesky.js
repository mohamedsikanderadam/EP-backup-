jQuery(function($){
	"use strict";
	
	ts_register_carousel( null, $ );
	
	/*** Load Products In Category Tab ***/
	var ts_product_in_category_tab_data = [];
	
	/* Change tab */
	$('.ts-product-in-category-tab-wrapper .column-tabs .tab-item, .ts-product-in-product-type-tab-wrapper .column-tabs .tab-item').on('click', function(){
		var element = $(this).parents('.ts-product-in-category-tab-wrapper');
		var is_product_type_tab = false;
		if( element.length == 0 ){
			element = $(this).parents('.ts-product-in-product-type-tab-wrapper');
			is_product_type_tab = true;
		}
		
		var element_top = element.offset().top;
		if( element_top > $(window).scrollTop() ){
			var admin_bar_height = $('#wpadminbar').length > 0?$('#wpadminbar').outerHeight():0;
			var sticky_height = $('.is-sticky .header-sticky').length > 0?$('.is-sticky .header-sticky').outerHeight():0;
			$('body, html').animate({
				scrollTop: element_top - sticky_height - admin_bar_height - 20
			}, 500);
		}
		
		if( $(this).hasClass('current') || element.find('.column-products').hasClass('loading') ){
			return;
		}
		
		element.removeClass('generated-slider');
		
		var element_id = element.attr('id');
		var atts = element.data('atts');
		if( !is_product_type_tab ){
			var product_cat = $(this).data('product_cat');
			var shop_more_link = $(this).data('link');
			var is_general_tab = $(this).hasClass('general-tab')?1:0;
		}
		else{
			var product_cat = atts.product_cats;
			var is_general_tab = 0;
			atts.product_type = $(this).data('product_type');
			element.find('.column-products').removeClass('recent sale featured best_selling top_rated mixed_order').addClass(atts.product_type);
		}
		
		if( !is_product_type_tab && element.find('a.shop-more-button').length > 0 ){
			element.find('a.shop-more-button').attr('href', shop_more_link);
		}
		
		element.find('.column-tabs .tab-item').removeClass('current');
		$(this).addClass('current');
		
		/* Check cache */
		var tab_data_index = element_id + '-' + product_cat.toString().split(',').join('-');
		if( is_product_type_tab ){
			tab_data_index += '-' + atts.product_type;
		}
		if( ts_product_in_category_tab_data[tab_data_index] != undefined ){
			element.find('.column-products .products').remove();
			element.find('.column-products').append( ts_product_in_category_tab_data[tab_data_index] ).hide().fadeIn(600);
			
			/* Shop more button handle */
			if( !is_product_type_tab ){
				ts_product_in_category_tab_shop_more_handle( element, atts );
			}
			
			/* Generate slider */
			ts_register_carousel( element.parent(), $ );
			
			return;
		}
		
		element.find('.column-products').addClass('loading');
		
		$.ajax({
			type : "POST",
			timeout : 30000,
			url : themesky_params.ajax_uri,
			data : {action: 'ts_get_product_content_in_category_tab', atts: atts, product_cat: product_cat, is_general_tab: is_general_tab},
			error: function(xhr,err){
				
			},
			success: function(response) {
				if( response ){
					element.find('.column-products .products').remove();
					element.find('.column-products').append( response ).hide().fadeIn(600);
					/* save cache */
					if( element.find('.counter-wrapper').length == 0 ){
						ts_product_in_category_tab_data[tab_data_index] = response;
					}
					else{
						ts_counter( element.find('.counter-wrapper') );
					}
					/* Shop more button handle */
					if( !is_product_type_tab ){
						ts_product_in_category_tab_shop_more_handle( element, atts );
					}
					/* Generate slider */
					ts_register_carousel( element.parent(), $ );
				}
				element.find('.column-products').removeClass('loading');
			}
		});
	});
	
	function ts_product_in_category_tab_shop_more_handle(element, atts){
		var hide_shop_more = element.find('.hide-shop-more').length;
		element.find('.hide-shop-more').remove();
		
		if( element.find('.tab-item.current').hasClass('general-tab') && atts.show_shop_more_general_tab == 0 ){
			hide_shop_more = true;
		}
		
		if( element.find('.products .product').length == 0 ){
			hide_shop_more = true;
		}
		
		if( atts.show_shop_more_button == 1 ){
			if( hide_shop_more ){
				element.find('.shop-more').addClass('hidden');
				element.removeClass('has-shop-more-button');
			}
			else{
				element.find('.shop-more').removeClass('hidden');
				element.addClass('has-shop-more-button');
			}
		}
	}
	
	$('.ts-product-in-category-tab-wrapper').each(function(){
		var element = $(this);
		var atts = element.data('atts');
		ts_product_in_category_tab_shop_more_handle( element, atts );
	});
	
	setTimeout(function(){
		/*** Blog Shortcode ***/
		$('.ts-blogs-wrapper.ts-shortcode').each(function(){
			var element = $(this);
			var atts = element.data('atts');
			
			var is_masonry = typeof $.fn.isotope == 'function' && element.hasClass('ts-masonry') ? true : false;
			
			/* Show more */
			element.find('a.load-more').on('click', function(){
				var button = $(this);
				if( button.hasClass('loading') ){
					return false;
				}
				
				button.addClass('loading');
				var paged = button.attr('data-paged');
				var total_pages = button.attr('data-total_pages');
				
				$.ajax({
					type : "POST",
					timeout : 30000,
					url : themesky_params.ajax_uri,
					data : {action: 'ts_blogs_load_items', paged: paged, atts : atts},
					error: function(xhr,err){
						
					},
					success: function(response) {
						if( paged == total_pages ){
							button.parent().remove();
						}
						else{
							button.removeClass('loading');
							button.attr('data-paged', ++paged);
						}
						if( response != 0 && response != '' ){
							if( is_masonry ){										
								element.find('.blogs').isotope('insert', $(response));
								setTimeout(function(){
									element.find('.blogs').isotope('layout');
								}, 500);
							}
							else{
								element.find('.blogs').append(response);
							}
							
							ts_register_carousel( element.parent(), $ );
						}
						else{ /* No results */
							button.parent().remove();
						}
					}
				});
				
				return false;
			});
			
		});
		
		/*** Reload SoundCloud ***/
		$('.owl-item .ts-soundcloud iframe').each(function(){
			var iframe = $(this);
			var src = iframe.attr('src');
			iframe.attr('src', src);
		});
	}, 200);
	
	/*** Counter ***/
	function ts_counter( elements ){
		if( elements.length > 0 ){
			var interval = setInterval(function(){
				elements.each(function(index, element){
					var wrapper = $(element);
					var second = parseInt( wrapper.find('.seconds .number').text() );
					if( second > 0 ){
						second--;
						second = ( second < 10 )? zeroise(second, 2) : second.toString();
						wrapper.find('.seconds .number').text(second);
						return;
					}
					
					var delta = 0;
					var time_day = 60 * 60 * 24;
					var time_hour = 60 * 60;
					var time_minute = 60;
					
					var day = parseInt( wrapper.find('.days .number').text() );
					var hour = parseInt( wrapper.find('.hours .number').text() );
					var minute = parseInt( wrapper.find('.minutes .number').text() );
					
					if( day != 0 || hour != 0  || minute != 0 || second != 0 ){
						delta = (day * time_day) + (hour * time_hour) + (minute * time_minute) + second;
						delta--;
						
						day = Math.floor(delta / time_day);
						delta -= day * time_day;
						
						hour = Math.floor(delta / time_hour);
						delta -= hour * time_hour;
						
						minute = Math.floor(delta / time_minute);
						delta -= minute * time_minute;
						
						second = delta > 0?delta:0;
						
						day = ( day < 10 )? zeroise(day, 2) : day.toString();
						hour = ( hour < 10 )? zeroise(hour, 2) : hour.toString();
						minute = ( minute < 10 )? zeroise(minute, 2) : minute.toString();
						second = ( second < 10 )? zeroise(second, 2) : second.toString();
						
						wrapper.find('.days .number').text(day);
						wrapper.find('.hours .number').text(hour);
						wrapper.find('.minutes .number').text(minute);
						wrapper.find('.seconds .number').text(second);
					}
					
				});
			}, 1000);
		}
	}
	
	ts_counter( $('.product .counter-wrapper, .ts-countdown .counter-wrapper') );
	
	/*** Portfolio ***/
	$('.ts-portfolio-wrapper .load-more').on('click', function(){
		var element = $(this).parents('.ts-portfolio-wrapper');
		var atts = element.data('atts');
		var button = $(this);
		if( button.hasClass('loading') ){
			return false;
		}
		
		button.addClass('loading');
		var paged = button.attr('data-paged');
		var total_pages = button.attr('data-total_pages');
		
		$.ajax({
			type : "POST",
			timeout : 30000,
			url : themesky_params.ajax_uri,
			data : {action: 'ts_portfolio_load_items', paged: paged, atts : atts},
			error: function(xhr,err){
				
			},
			success: function(response) {
				if( paged == total_pages ){
					button.parent().remove();
				}
				else{
					button.removeClass('loading');
					button.attr('data-paged', ++paged);
				}
				if( response != 0 && response != '' ){
					if( typeof $.fn.isotope == 'function' ){										
						element.find('.portfolio-inner').isotope('insert', $(response));
						element.find('.filter-bar li.current').trigger('click');
						setTimeout(function(){
							element.find('.portfolio-inner').isotope('layout');
						}, 500);
					}
				}
				else{ /* No results */
					button.parent().remove();
				}
			}
		});
		
		return false;
	});
	
	$('.ts-portfolio-wrapper .filter-bar li').on('click', function(){
		$(this).siblings('li').removeClass('current');
		$(this).addClass('current');
		var container = $(this).parents('.ts-portfolio-wrapper').find('.portfolio-inner');
		var data_filter = $(this).data('filter');
		container.isotope({filter: data_filter});
	});
	
	/* Update like */
	$(document).on('click', '.ts-portfolio-wrapper .portfolio-thumbnail .like, .single-portfolio .portfolio-like .ic-like', function(e){
		var _this = $(this);
		
		if( _this.hasClass('loading') ){
			return false;
		}
		_this.addClass('loading');
		
		var already_like = _this.hasClass('already-like');
		var is_single = _this.hasClass('ic-like');
		
		var post_id = _this.data('post_id');
		$.ajax({
			type : "POST",
			timeout : 30000,
			url : themesky_params.ajax_uri,
			data : {action: 'ts_portfolio_update_like', post_id: post_id},
			error: function(xhr,err){
				_this.removeClass('loading');
			},
			success: function(response) {
				if( response != '' ){
					if( already_like ){
						_this.removeClass('already-like');
						if( !is_single ){
							_this.attr('title', _this.data('like-title'));
						}
					}
					else{
						_this.addClass('already-like');
						if( !is_single ){
							_this.attr('title', _this.data('liked-title'));
						}
					}
					if( is_single ){
						var single_plural = '1' == response ? 'single' : 'plural';
						response += ' ' + _this.siblings('.like-num').data(single_plural);
						_this.siblings('.like-num').text(response);
					}
				}
				_this.removeClass('loading');
			}
		});
		
		return false;
	});
	
	/*** Widgets ***/
	/* Custom WP Widget Categories Dropdown */
	$('.widget_categories > ul').each(function(index, ele){
		var _this = $(ele);
		var icon_toggle_html = '<span class="icon-toggle"></span>';
		var ul_child = _this.find('ul.children');
		ul_child.hide();
		ul_child.closest('li').addClass('cat-parent');
		ul_child.before( icon_toggle_html );
	});
	
	$('.widget_categories span.icon-toggle').on('click', function(){
		var parent_li = $(this).parent('li.cat-parent');
		if( !parent_li.hasClass('active') ){
			parent_li.find('ul.children:first').slideDown();
			parent_li.addClass('active');
		}
		else{
			parent_li.find('ul.children').slideUp();
			parent_li.removeClass('active');
			parent_li.find('li.cat-parent').removeClass('active');
		}
	});
	
	$('.widget_categories li.current-cat').parents('ul.children').siblings('.icon-toggle').trigger('click');
	$('.widget_categories li.current-cat.cat-parent > .icon-toggle').trigger('click');
	
	/* Product Categories widget */
	$('.ts-product-categories-widget .icon-toggle').on('click', function(){
		var parent_li = $(this).parent('li.cat-parent');
		if( !parent_li.hasClass('active') ){
			parent_li.addClass('active');
			parent_li.find('ul.children:first').slideDown();
		}
		else{
			parent_li.find('ul.children').slideUp();
			parent_li.removeClass('active');
			parent_li.find('li.cat-parent').removeClass('active');
		}
	});
	
	$('.ts-product-categories-widget').each(function(){
		var element = $(this);
		element.find('ul.children').parent('li').addClass('cat-parent');
		element.find('li.current.cat-parent > .icon-toggle').trigger('click');
		element.find('li.current').parents('ul.children').siblings('.icon-toggle').trigger('click');
	});
	
	/* Product Filter By Availability */
	$('.product-filter-by-availability-wrapper > ul input[type="checkbox"]').on('change', function(){
		$(this).parent('li').siblings('li').find('input[type="checkbox"]').attr('checked', false);
		var val = '';
		if( $(this).is(':checked') ){
			val = $(this).val();
		}
		var form = $(this).closest('ul').siblings('form');
		if( val != '' ){
			form.find('input[name="stock"]').val(val);
		}
		else{
			form.find('input[name="stock"]').remove();
		}
		form.submit();
	});
	
	/* Product Filter By Brand */
	$('.product-filter-by-brand-wrapper ul input[type="checkbox"]').on('change', function(){
		var wrapper = $(this).parents('.product-filter-by-brand-wrapper');
		var query_type = wrapper.find('> .query-type').val();
		var checked = $(this).is(':checked');
		var val = new Array();
		if( query_type == 'or' ){
			wrapper.find('ul input[type="checkbox"]').attr('checked', false);
			if( checked ){
				$(this).off('change');
				$(this).attr('checked', true);
				val.push( $(this).val() );
			}
		}
		else{
			wrapper.find('ul input[type="checkbox"]:checked').each(function(index, ele){
				val.push( $(ele).val() );
			});
		}
		val = val.join(',');
		var form = wrapper.find('form');
		if( val != '' ){
			form.find('input[name="product_brand"]').val( val );
		}
		else{
			form.find('input[name="product_brand"]').remove();
		}
		form.submit();
	});
});

function zeroise( str, max ){
	str = str.toString();
	return str.length < max ? zeroise('0' + str, max) : str;
}

class TS_Carousel{
	register( $scope, $ ){
		var carousel = this;
		
		/* [wrapper selector, slider selector, slider options (remove dynamic columns at last)] */
		var data = [
			['.ts-product-wrapper', '.products']
			,['.ts-product-deals-wrapper', '.products']
			,['.ts-product-category-wrapper', '.products', { responsive:{0:{items:1},300:{items:2},700:{items:3}} }]
			,['.ts-product-brand-wrapper', '.content-wrapper', { responsive:{0:{items:1},300:{items:2},700:{items:3}} }]
			,['.ts-products-widget-wrapper', null, { margin: 10, responsive:{0:{items:1}} }]
			,['.ts-blogs-wrapper', '.content-wrapper > .blogs', { responsive:{0:{items:1},570:{items:2},700:{items:3}} }]
			,['.ts-logo-slider-wrapper', '.items', { responsive:{0:{items:1},300:{items:2},400:{items:3},640:{items:4},930:{items:5}} }]
			,['.ts-team-members', '.items', { responsive:{0:{items:1},500:{items:2},800:{items:3}} }]
			,['.ts-instagram-wrapper', null, { responsive: {0:{items:1},320:{items:2},500:{items:3},700:{items:4}} }]
			,['.ts-twitter-slider, .ts-testimonial-wrapper', '.items', { animateIn: 'fadeIn', animateOut: 'fadeOut', responsive: {0:{items:1}} }]
			,['.ts-portfolio-wrapper', '.portfolio-inner', { responsive: {0:{items:1},500:{items:2},900:{items:3}} }]
			,['.ts-blogs-widget-wrapper', null, { margin: 10, responsive: {0:{items:1}} }]
			,['.ts-recent-comments-widget-wrapper', null, { margin: 10, responsive: {0:{items:1}} }]
			,['.ts-product-in-category-tab-wrapper, .ts-product-in-product-type-tab-wrapper', '.products', { responsive:{0:{items:1},320:{items:2},580:{items:3}} }]
			,['.ts-blogs-wrapper .thumbnail.gallery', 'figure', { nav: true, animateIn: 'fadeIn', animateOut: 'fadeOut', margin: 10, mouseDrag: false, touchDrag: false, responsive:{0:{items:1}} }]
		];
		
		$.each(data, function(index, value){
			carousel.run( value, $ );
		});
	}
	
	run( data, $ ){
		$(data[0]).each(function(){
			if( ! $(this).hasClass('ts-slider') || $(this).hasClass('generated-slider') ){
				return;
			}
			$(this).addClass('generated-slider');
			
			var element = $(this);
			var show_nav = typeof element.attr('data-nav') != 'undefined' && element.attr('data-nav') == 1?true:false;
			var show_dots = typeof element.attr('data-dots') != 'undefined' && element.attr('data-dots') == 1?true:false;
			var auto_play = typeof element.attr('data-autoplay') != 'undefined' && element.attr('data-autoplay') == 1?true:false;
			var columns = typeof element.attr('data-columns') != 'undefined'?parseInt(element.attr('data-columns')):5;
			var disable_responsive = typeof element.attr('data-disable_responsive') != 'undefined' && element.attr('data-disable_responsive') == 1?true:false;
			var prev_nav_text = typeof element.attr('data-prev_nav_text') != 'undefined'?element.attr('data-prev_nav_text'):'';
			var next_nav_text = typeof element.attr('data-next_nav_text') != 'undefined'?element.attr('data-next_nav_text'):'';
			var responsive_base = typeof data[1] != 'undefined' && data[1] != null ? element.find(data[1]) : element;
			
			var slider_options = {
						loop: true
						,nav: show_nav
						,navText: [prev_nav_text, next_nav_text]
						,dots: show_dots
						,navSpeed: 1000
						,rtl: $('body').hasClass('rtl')
						,margin: 0
						,navRewind: false
						,autoplay: auto_play
						,autoplayHoverPause: true
						,autoplaySpeed: 1000
						,responsiveBaseElement: responsive_base
						,responsiveRefreshRate: 400
						,responsive:{0:{items:1},320:{items:2},580:{items:3},820:{items:columns}}
						,onInitialized: function(){
							element.removeClass('loading');
							element.find('.loading').removeClass('loading');
						}
					};
			
			if( typeof data[2] != 'undefined' && data[2] != null ){
				$.extend( slider_options, data[2] );
				
				if( typeof data[2].responsive != 'undefined' ){ /* change responsive => add dynamic columns at last */
					switch( data[0] ){
						case '.ts-blogs-wrapper':
							slider_options.responsive[870] = {items:columns};
						break;
						case '.ts-product-category-wrapper':
						case '.ts-product-brand-wrapper':
							slider_options.responsive[871] = {items:columns};
						break;
						case '.ts-team-members':
							slider_options.responsive[930] = {items:columns};
						break;
						case '.ts-instagram-wrapper':
						case '.ts-portfolio-wrapper':
							slider_options.responsive[1170] = {items:columns};
						break;
						case '.ts-product-in-category-tab-wrapper, .ts-product-in-product-type-tab-wrapper':
							slider_options.responsive[820] = {items:columns};
						break;
						default:
					}
				}
			}
			
			if( element.hasClass('use-logo-setting') ){ /* Product Brands - Logos */
				var break_point = element.data('break_point');
				var item = element.data('item');
				if( break_point.length > 0 ){
					slider_options.responsive = {};
					for( var i = 0; i < break_point.length; i++ ){
						slider_options.responsive[break_point[i]] = {items: item[i]};
					}
				}
			}
			
			if( disable_responsive ){
				slider_options.responsive = {0:{items:columns}};
			}
			
			if( columns == 1 ){
				slider_options.responsive = {0:{items:1},320:{items:2},700:{items:3}};
			}
			
			if( data[0] == '.ts-blogs-wrapper' ){
				switch( columns ){
					case '1':
						slider_options.responsive = {0:{items:columns}};
					break;
					case '2':
						slider_options.responsive = {0:{items:1},700:{items:columns}};
					break;
					default:
						slider_options.responsive = {0:{items:1},700:{items:2},1000:{items:columns}};
					break;
				}
			}
			
			if( typeof data[1] != 'undefined' && data[1] != null ){
				element.find(data[1]).owlCarousel( slider_options );
			}
			else{
				element.owlCarousel( slider_options );
			}
		});
	}
}

function ts_register_carousel( $scope, $ ){
	var carousel = new TS_Carousel();
	carousel.register( $scope, $ );
}

function ts_register_masonry( $scope, $ ){
	if( typeof $.fn.isotope == 'function' ){
		/* Blog */
		$('.ts-blogs-wrapper.ts-masonry .blogs').isotope();
		$('.ts-blogs-wrapper.ts-masonry').removeClass('loading');
		
		/* Portfolio */
		$('.ts-portfolio-wrapper.ts-masonry .portfolio-inner').isotope({filter: '*'});
		$('.ts-portfolio-wrapper.ts-masonry').removeClass('loading');
	}
}

jQuery(window).on('elementor/frontend/init', function(){
	var elements = ['ts-products', 'ts-product-deals', 'ts-product-categories', 'ts-product-brands', 'ts-blogs'
					,'ts-logos', 'ts-team-members', 'ts-twitter-slider', 'ts-testimonial', 'ts-portfolios'
					,'ts-products-in-category-tabs', 'ts-products-in-product-type-tabs'
					,'wp-widget-ts_products', 'wp-widget-ts_blogs', 'wp-widget-ts_recent_comments', 'wp-widget-ts_instagram'];
	jQuery.each(elements, function(index, name){
		elementorFrontend.hooks.addAction( 'frontend/element_ready/' + name + '.default', ts_register_carousel );
	});
	
	elements = ['ts-blogs', 'ts-portfolios'];
	jQuery.each(elements, function(index, name){
		elementorFrontend.hooks.addAction( 'frontend/element_ready/' + name + '.default', ts_register_masonry );
	});
});