/* АВТОЗАПОЛЕНИЕ ПОЛЕ АДРЕС */
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
/* АВТОЗАПОЛЕНИЕ ПОЛЕ АДРЕС */

/* АВТОЗАПОЛЕНИЕ ПОЛЕ ЗАКАЗА */
$(document).ready( function() {
    $('#step_4').on('click', function () {
            calculateOrder()
        })
    });
function calculateOrder (){
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
            var comment = $('#comment').val()
            var total_item_cost = parseFloat($('span[id="total_item_cost"]').text())
            var deliveryExpress = parseFloat($('#express_delivery_price').val())
            var deliverStandard = parseFloat($('#fees').val())
            if (deliveryValue == 'express') {
                $('#total_sum').val('');
                $('#total_cost').text('');
                $('#delivery_express_block').show();
                $('#delivery_cost').html($('#express_delivery_price').val());
                $('#delivery_cost_span').addClass("express_delivery_label");
                $('#total_sum').val(total_item_cost+deliverStandard+deliveryExpress)
                var t = $('#total_sum').val()
                console.log(`TOTAL =${t} `)
                $('#total_cost').text(total_item_cost+deliverStandard+deliveryExpress)
            } else {
                $('#delivery_cost_span').removeClass("express_delivery_label");
                $('#delivery_cost').text('');
                $('#total_sum').val('')
                $('#total_cost').text('')
                $('#delivery_express_block').attr('style', 'display:none');
                $('#total_sum').val(total_item_cost+deliverStandard);
                $('#total_cost').text(`${total_item_cost+deliverStandard},00`);
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
/* АВТОЗАПОЛЕНИЕ ПОЛЕ ЗАКАЗА  */

/* АВТОФОРМАТИРОВАНИЕ НОМЕРА ТЕЛЕФОНА */
$(document).ready(function() {
    var tel = $('#phone_formatter').text()
    var telephone = '+7 ('+`${tel[0]}`+`${tel[1]}`+`${tel[3]}`+') '+
                           `${tel[4]}`+`${tel[4]}`+`${tel[5]}`+'-'+
                           `${tel[6]}`+`${tel[7]}`+'-'+
                           `${tel[8]}`+`${tel[9]}`

    $('#phone_formatter').html(telephone);
});
/* АВТОФОРМАТИРОВАНИЕ НОМЕРА ТЕЛЕФОНА */

/* РАССКРЫТИЕ КОММЕНТАРИЕВ */
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
/* РАССКРЫТИЕ КОММЕНТАРИЕВ */

/* ОПЛАТА ТОВАРА */
$('#form').submit(function () {
    $('#spinner').attr('style', 'display:block');
    $('#form_container').attr('style', 'display:none');
    $.ajax({
        data: $(this).serialize(),
        url: `/order/validate_username/`,
        method: "POST",
        success: function (response) {
            setTimeout(function() {
                    getStatus(response.task_id, response.order_id);
                    }, 1000);
                },
        error: function (response) {
           window.location.href = response.failed_url
        }
    });
    return false;
});
/* ОПЛАТА ТОВАРА */

/* ПРОВЕРКА СТАТУСА ОПЛАТЫ ТОВАРА */
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
/* ПРОВЕРКА СТАТУСА ОПЛАТЫ ТОВАРА */

/* ПРОВЕРКА СТАТУСА ОПЛАТЫ ТОВАРА */
$( document ).ready(function() {

});
/* ПРОВЕРКА СТАТУСА ОПЛАТЫ ТОВАРА */