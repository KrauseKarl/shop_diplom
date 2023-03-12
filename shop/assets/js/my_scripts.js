/* АВТОЗАПОЛЕНИЕ ПОЛЕ ЗАКАЗА */


$(function getAddress() {
 $("#post_address").on("change", function () {
    var post_address = $('#post_address').val()
    if (typeof post_address != "undefined") {
    var wholeAddress  = new String(post_address)
    var addressArray =  wholeAddress.split(';')
    var city = addressArray[0];
    var address = addressArray[1];
    $('#city').val(city);
    $('#address').val(address);
    }
    });
});

$(document).ready( function() {
    $('#step_4').on('click', function () {
            var deliveryValue = $('input[name="delivery"]:checked').val();
            var delivery = $('span[id="'+deliveryValue+'"]').text()
            var payValue = $('input[name="pay"]:checked').val();
            var pay = $('span[id="'+payValue+'"]').text()
            var name = $('#name').val()
            var telephone = $('#telephone').val()
            var email = $('#email').val()
            var post_address = $('#post_address').val()
            var city = $('#city').val()
            var address = $('#address').val()
            var total_cost = $('#total_cost').text()
            var deliveryFees = $('#express_delivery_price').val()
            var comment = $('#comment').val()
            console.log($('#express_delivery_price').val())
            console.log(deliveryValue)
            console.log(delivery)
            console.log(total_cost)
            var total = $('#total_sum').val(parseFloat(total_cost)+parseFloat($('#express_delivery_price').val())+parseFloat($('#fees').text()))
            console.log(total.val())

            if (deliveryValue == 'express') {
                $('#delivery_cost').html($('#express_delivery_price').val())
                console.log($('#delivery_cost').text())
                $('#delivery_cost_span').addClass("express_delivery_label")

                $('#total_sum').val(total)
                $('#total_cost').text(parseFloat(total_cost)+parseFloat($('#express_delivery_price').val())+parseFloat($('#fees').text()))
            } else {
                $('#delivery_express_block').css("display", "none");
                $('#total_sum').val(parseFloat(total_cost)+parseFloat($('#fees').text()))
                $('#total_cost').text(parseFloat(total_cost)+parseFloat($('#fees').text()))
            }

            $('#name_result').text($('#name').val());
            $('#telephone_result').html(telephone);
            $('#email_result').html($('#email').val());
            $('#city_result').text($('#city').val());
            $('#address_result').html($('#address').val());
            $('#delivery_result').html(delivery);
            $('#pay_result').html(pay);
            $('#comment_result').html($('#comment').val())

        }
    )
    }
);
/* АВТОЗАПОЛЕНИЕ ПОЛЕ ЗАКАЗА END */

$(document).ready(function() {
    var tel = $('#phone_formatter').text()
    var telephone = '+7 ('+`${tel[0]}`+`${tel[1]}`+`${tel[3]}`+') '+
                           `${tel[4]}`+`${tel[4]}`+`${tel[5]}`+'-'+
                           `${tel[6]}`+`${tel[7]}`+'-'+
                           `${tel[8]}`+`${tel[9]}`

    $('#phone_formatter').html(telephone);
});

//
$(document).ready(function() {
    var totalPrice = parseFloat($('#total_price').data('value'))
    var totalFees = parseFloat($('#total_fees').data('value'))

    $('#order_button').text(totalPrice+totalFees)
    $('#modal_total_price').text(totalPrice+totalFees)
    $('#total_price_with_delivery').text(totalPrice+totalFees)
    $('#total_price_with_delivery').val(totalPrice+totalFees)
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
function getStatus(orderID, taskID) {
  $.ajax({
    url: `/order/get_status_payment/${taskID}/${orderID}/`,
    method: 'GET'
  })
  .done((response) => {
    const taskStatus = response.task_status;
    if (taskStatus === 'ERROR' || taskStatus === 'FAILURE'){
        console.log(`FAILURE WINDOW`)
        window.location.href = response.failed_url
    }
    else if (taskStatus === 'SUCCESS') {
        console.log(`SUCCESS WINDOW`)
        window.location.href = response.success_url
    }
    else {
       console.log(`STATUS = ${taskStatus}`)
       setTimeout(function() {
            getStatus(response.task_id, response.order_id);
            }, 1000);
       }  return false;
  })
  .fail((err) => {
    console.log(err)
  });
}


$('#form').submit(function () {
    $('#spinner').attr('style', 'display:block');
    $('#form').attr('style', 'display:none');
    $.ajax({
        data: $(this).serialize(),
        url: `/order/validate_username/`,
        method: "POST",
        success: function (response) {
                console.log(`START`)
                console.log(`task_status = ${response.task_status}`)
                console.log(`task_result = ${response.task_result}`)
                console.log(response.task_id)
                console.log(`FINISH`)
            setTimeout(function() {
                    getStatus(response.task_id, response.order_id);
                    }, 1000);
                },
        error: function (response) {
            console.log(response.responseJSON.errors)
        }
    });
    return false;
});
