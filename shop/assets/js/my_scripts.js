/* АВТОЗАПОЛЕНИЕ ПОЛЕ ЗАКАЗА */

$(document).ready( function() {
    $('#step_4').on('click', function () {
            var deliveryValue = $('input[name="delivery"]:checked').val();
            var delivery = $('span[id="'+deliveryValue+'"]').text()
            var payValue = $('input[name="pay"]:checked').val();
            var pay = $('span[id="'+payValue+'"]').text()
            var name = $('#name').val()
            var t = $('#telephone').val()
            var email = $('#email').val()
            var city = $('#city').val()
            var address = $('#address').val()
            var total_cost = $('#total_cost').text()
            var deliveryFees = $('#delivery_normal_cost').text()

            if (delivery == 'Экспресс доставка') {
                $('#delivery_cost').text('20')
                $('#total_sum').val(parseFloat(total_cost)+parseFloat($('#delivery_cost').text())+parseFloat($('#fees').text()))
                $('#total_cost').text(parseFloat(total_cost)+parseFloat($('#delivery_cost').text())+parseFloat($('#fees').text()))
            } else {
                $('#total_sum').val(parseFloat(total_cost)+parseFloat($('#fees').text()))
                $('#total_cost').text(parseFloat(total_cost)+parseFloat($('#fees').text()))
            }
            var telephone = '+7 ('+`${t[0]}`+`${t[1]}`+`${t[3]}`+') '+
                                   `${t[4]}`+`${t[4]}`+`${t[5]}`+'-'+
                                   `${t[6]}`+`${t[7]}`+'-'+
                                   `${t[8]}`+`${t[9]}`
            $('#name_result').text($('#name').val());
            $('#telephone_result').html(telephone);
            $('#email_result').html($('#email').val());
            $('#city_result').text($('#city').val());
            $('#address_result').html($('#address').val());
            $('#delivery_result').html(delivery)
            $('#pay_result').html(pay)
        }
    )
    }
);
/* АВТОЗАПОЛЕНИЕ ПОЛЕ ЗАКАЗА END */


//
$(document).ready(function() {
    var totalPrice = parseFloat($('#total_price').data('value'))
    console.log('totalPrice=', $('#total_price'))
    var totalFees = parseFloat($('#total_fees').data('value'))

     console.log(totalFees)
    $('#order_button').text(totalPrice+totalFees)
    $('#modal_total_price').text(totalPrice+totalFees)
    $('#total_price_with_delivery').text(totalPrice+totalFees)
    $('#total_price_with_delivery').value(totalPrice+totalFees)
     console.log($('#total_price_with_delivery'))
    }
)
//

// РАССКРЫТИЕ КОММЕНТАРИЕВ
$( document ).ready(function() {

    $(".Comment:gt(0)").addClass('Comment-hidden');
    if($(".Comment").length > 1) {
        $("#show_comment").css('display','block').html('Показать еще '+ $(".Comment-hidden").length);
        $("#hide_comment").css('display','none');
    } else {
        $("#show_comment").css('display','none');
        $("#hide_comment").css('display','none');
    }

    $('#show_comment').on('click', function () {
        $('.Comment-hidden').each(function (index) {
            if (index < 2) {
                $(this).slideDown('slow', function () {
                    $(this).removeClass('Comment-hidden').addClass('Comment-show');
                    $('#show_comment').html('Показать еще '+ $('.Comment-hidden').length)
                    }
                );
            }
        }
        );
        if ($('.Comment-hidden').length < 3) {
            $('#show_comment').css('display', 'none');
            $('#hide_comment').css('display', 'block');
        }

    });

    $('#hide_comment').on('click', function() {
        $(".Comment:gt(0)").slideUp('slow', function () {
            $(this).removeClass('Comment-show').addClass('Comment-hidden');
            }
        );
        $("#hide_comment").css('display','none');
        $("#show_comment").css('display','block');
        $("#show_comment").html('Показать еще ');
        }
    );
});
//  РАССКРЫТИЕ КОММЕНТАРИЕВ END

// ПАГИНАЦИЯ
//function ajaxPagination() {
//    $('.Pagination.Pagination-ins a.Pagination-element').each((index, el) =>
//        $(el).click(e) => {
//        e.preventDefault()
//        let page_url = $(e).attr('href')
//        console.log( page_url )
//
//        $.ajax({
//            url: page_url,
//            type: 'GET',
//            success: (data) => {
//            $('.Cards').empty()
//            $('.Cards').append($(data).filter('.Cards').html() )
//
//            $('.Pagination').empty()
//            $('.Pagination').append($(data).filter('.Pagination').html() )
//            alert('Pagination is working!')
//            }
//        })
//        }
//    )
//}
//$(document).ready(function() {
//    ajaxPagination()
//})
//
//$(document).ajaxStop(function() {
//    ajaxPagination()
//})

// ПАГИНАЦИЯ END


//
//$('#p_create_tag').on('click', function () {
//    const addTag = $('#p_create_tag')
//    const href = $('#p_create_tag').attr('href')
//    const win = window.open('/store/add_tag/', '_blank', 'left=450,top=150,height=480,width=640,resizable=yes,scrollbars=yes');
//    win.focus();
//})

// POST-запрос из модального окна
var tagForm = $('#tagCreateForm');
var inputTag =  $('input[id="new_tag_title"]').val()
//inputTag.reset();
tagForm.submit(function () {
    $.ajax({
        type: tagForm.attr('method'),
        url: tagForm.attr('action'),
        data: tagForm.serialize(),
        success: function (data) {
            $("#result").html("тег "+data['title']+" добавлен");
            $('[href="#openModal"]').hidden()
        },
        error: function(data) {
            $("#result").html("Something went wrong!");
        }
    });
    return false;
});

//document.querySelector('#price_desc').style.display = 'none';
///* SORT BY PRICE ASCEND */
//document.querySelector('#price_asc').onclick = function() {
//    itemSortByAsc("data-price");
//}
///* SORT BY PRICE DESCEND */
//document.querySelector('#price_desc').onclick = function() {
//    itemSortByDesc("data-price")
//}
///* SORT BY VIEWS DESCEND */
//document.querySelector('#views_desc').onclick = function() {
//    itemSortByDesc("data-views");
//}
///* SORT BY COMMENTS DESCEND */
//document.querySelector('#comments_desc').onclick = function() {
//    itemSortByDesc("data-comments");
//}

///* FUNCTION TO SORT FROM MAX TO MIN RESULT */
//function itemSortByAsc(sortValue) {
//    let cards = document.querySelector('#all_cards');
//    let arrow_asc = document.querySelector('#price_asc');
//    let arrow_desc = document.querySelector('#price_desc');
//    arrow_asc.parentNode.classList.remove("Sort-sortBy_inc");
//    arrow_asc.parentNode.classList.add("Sort-sortBy_dec");
//    arrow_desc.style.display="block";
//    arrow_asc.style.display="none";
//    for (let i = 0; i < cards.children.length; i++) {
//        for (let j = i; j < cards.children.length; j++) {
//            if (+cards.children[i].getAttribute(sortValue) > +cards.children[j].getAttribute(sortValue)) {
//            replacedNode = cards.replaceChild(cards.children[j],cards.children[i]);
//            insertAfter(replacedNode, cards.children[i]);
//            }
//        }
//    }
//}
///* FUNCTION TO SORT FROM MIN TO MAX RESULT */
//function itemSortByDesc(sortValue) {
//    let cards = document.querySelector('#all_cards');
//    let arrow_asc = document.querySelector('#price_asc');
//    let arrow_desc = document.querySelector('#price_desc');
//    arrow_desc.parentNode.classList.remove("Sort-sortBy_dec");
//    arrow_desc.parentNode.classList.add("Sort-sortBy_inc");
//    arrow_desc.style.display="none";
//    arrow_asc.style.display="block";
//
//    for (let i = 0; i < cards.children.length; i++) {
//        for (let j = i; j < cards.children.length; j++) {
//            if (+cards.children[i].getAttribute(sortValue) < +cards.children[j].getAttribute(sortValue)) {
//            replacedNode = cards.replaceChild(cards.children[j],cards.children[i]);
//            insertAfter(replacedNode, cards.children[i]);
//            }
//        }
//    }
//}
//
//function insertAfter(newNode, referenceNode) {
//    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
//}

/* AJAX POST REQUEST TO UPDATE ITEM'S QUANTITY */
//$(document).on("click", "#update-button-add", function (e) {
//e.preventDefault();
//var prodid = $(this).data("index");
//var csrftoken = $('#csrftoken'+prodid).val();
//var productTotalPrice = $('#total_price_'+$(this).data("index")).data('value')
//console.log('prodid = '+prodid)
//console.log('productTotalPrice = '+productTotalPrice)
//console.log(csrftoken)
//    $.ajax({
//          type: "POST",
//          url: "/cart/update/",
//          headers: {'X-CSRFToken': csrftoken },
//          mode : 'same-origin',
//          data: {
//            productid: $(this).data("index"),
//            productqty: $("#input"+$(this).data("index")).val(),
//            prodprice: $('#price_'+$(this).data("index")).data('value'),
//            productTotalPrice: $('#total_price_'+$(this).data("index")).data('value'),
//            csrfmiddlewaretoken: csrftoken,
//            action: "post",
//          },
//          cache:false,
//          dataType: 'json',
//          success: function (json) {
//          total = parseFloat(json.productqty) * parseFloat(json.prodprice)
//          $('#total_price'+json.productid).innerHTML = total
//            },
//  error: function (xhr, errmsg, err) {},
//}
//);});
/* AJAX POST REQUEST TO UPDATE ITEM'S QUANTITY */

//let toast = document.getElementById("message");
//toast.delay(5000).remove()
//
//document.getElementById("close-button").addEventListener("click", function () {
//        toast.slideDown.remove()
//        });