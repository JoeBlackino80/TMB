"""Preklady webu (EN, ES, FR, AR, PT). Itinerár, PDF a e-maily ostávajú v angličtine —
sú určené ambasádam a leteckým kontrolám.

Použitie: šablóny dostanú slovník `t` podľa jazyka požiadavky
(?lang= → cookie → Accept-Language → en).
"""

STRINGS = {
    "en": {
        "pw_hint": "At least 10 characters. We also check that it hasn't appeared in a known data breach.",
        "google_btn": "Continue with Google", "or": "or",
        "link_btn": "E-mail me a sign-in link",
        "link_note": "No password needed — we send a one-time link, valid for 30 minutes.",
        "link_sent": "If an account exists for that e-mail, a sign-in link is on its way.",
        "link_confirm_text": "Click the button to finish signing in on this device.",
        "link_confirm_btn": "Sign in", "password_login": "Sign in with a password instead",
        "register_optional": "An account is optional — you can also order without one and"
            " sign in later with an e-mail link.",
        "guest_order_text": "No account needed: we create one for your e-mail automatically and"
            " you can sign in any time with a one-time e-mail link. Already have an account?",
        "needed_on_lbl": "Embassy appointment or check-in date (optional)",
        "needed_on_note": "Tell us when the reservation must be valid and we'll create it the"
            " evening before, so it is live on that day.",
        "calc_basic": "We'll create your reservation the evening before this date and e-mail it"
            " to you right away — it will be valid on the day.",
        "calc_week": "", "calc_twoweek": "More than 60 days away — order closer to the date,"
            " or choose the 14-day plan if you need it now.",
        "sample_btn": "See a sample document (PDF)",
        "hotel_soon_title": "Hotel reservations are coming soon.",
        "hotel_soon_text": "We are connecting our hotel booking partners. Flight reservations"
            " are available now.",
        "residency_lbl": "Guest nationality (passport country, 2 letters)",
        "residency_note": "Hotels price rates by the guest's country, e.g. SK, DE, IN.",
        "st_scheduled": "Payment received — reservation scheduled",
        "st_scheduled_text": "So that your reservation is valid on your date, we will create it"
            " and e-mail the itinerary on",
        "nav_privacy": "Privacy",
        "meta_title": "flight & hotel reservations for visa applications",
        "meta_description": "Unticketed flight reservations (PNR) and cancellable hotel"
            " reservations for visa applications and proof of onward travel, delivered"
            " by e-mail with a printable PDF.",
        "test_title": "TEST MODE.",
        "test_text": "Reservations created on this site are currently fictitious"
            " sandbox bookings: they do not exist in any airline's or hotel's system,"
            " cannot be verified and must NOT be used for a visa application. No"
            " payment is taken.",
        "operated_by": "Operated by", "company_id": "Company ID", "tax_id": "Tax ID",
        "vat_id": "VAT ID",
        "vat_note": "Prices include VAT.",
        "consent_html": "I request that the service starts immediately and acknowledge"
            " that I lose my right of withdrawal once the reservation has been"
            " delivered. I agree to the <a href='/terms'>Terms</a> and have read the"
            " <a href='/privacy'>Privacy policy</a>.",
        "hotel_badge1": "Real, cancellable reservation",
        "hotel_badge3": "PDF voucher + QR",
        "hotel_price_note": "per reservation, regardless of the number of nights.",
        "hotel_what_html": "<p>You receive a <b>real, cancellable hotel reservation</b>"
            " with a booking reference — held on a free-cancellation rate and released"
            " automatically before the cancellation deadline. It is supporting"
            " documentation for visa applications and proof of accommodation,"
            " <b>not a paid stay</b>.</p>",
        "st_verify_short": "Verify it on the airline's website under “Manage booking”"
            " with the PNR and passenger surname.",
        "st_sent_to": "The documents were also sent to",
        "st_test_confirmed": "TEST reservation — not valid, not verifiable",
        "st_refunded": "Reservation cancelled",
        "st_refunded_text": "The payment for this reservation was refunded or disputed,"
            " so the reservation was cancelled and will not be renewed.",
        "hotel_released": "was released before the free-cancellation deadline.",
        "nav_order": "Order", "nav_faq": "FAQ", "nav_terms": "Terms",
        "nav_login": "Sign in", "nav_account": "My account", "nav_logout": "Sign out",
        "nav_hotel": "Hotel",
        "hotel_hero_title": "A real hotel reservation for your visa",
        "hotel_hero_sub": "A <b>genuine, cancellable hotel reservation</b> with a"
            " confirmation number — held on a free-cancellation rate and delivered"
            " as a printable PDF. Perfect for <b>visa applications</b> and"
            " <b>proof of accommodation</b>.",
        "hotel_order_title": "Order your hotel reservation",
        "city_lbl": "Destination city", "checkin_lbl": "Check-in",
        "checkout_lbl": "Check-out", "guest": "Guest", "add_guest": "+ Add guest",
        "hotel_submit": "Get my hotel reservation",
        "hotel_confirmed": "Hotel reservation confirmed",
        "hotel_download": "Download PDF reservation",
        "checkin_th": "Check-in", "checkout_th": "Check-out", "hotel_th": "Hotel",
        "login_title": "Sign in", "register_title": "Create an account",
        "email_lbl": "E-mail", "password_lbl": "Password", "min8": "min. 8 characters",
        "login_btn": "Sign in", "register_btn": "Create account",
        "no_account": "No account yet?", "have_account": "Already have an account?",
        "forgot_link": "Forgot your password?",
        "forgot_title": "Reset your password",
        "forgot_text": "Enter your account e-mail and we'll send you a reset link.",
        "forgot_btn": "Send reset link",
        "forgot_sent": "If an account exists for that e-mail, a reset link is on its way.",
        "reset_title": "Set a new password", "new_password": "New password",
        "reset_btn": "Change password",
        "account_title": "My account", "order_history": "Order history",
        "th_date": "Date", "th_status": "Status", "view": "View",
        "no_orders": "No orders yet.",
        "saved_passengers": "Saved travellers",
        "saved_passengers_note": "Save traveller details to reuse them on future"
            " orders. Passport data is optional and stored encrypted.",
        "nationality": "Nationality", "passport": "Passport number",
        "passport_expiry": "Passport expiry", "add_saved_passenger": "Add a traveller",
        "passport_note": "Optional. Stored encrypted; used only to complete"
            " international reservations.",
        "delete": "Delete", "save": "Save",
        "new_order_btn": "New reservation", "traveller_saved": "Traveller saved.",
        "pw_len": "At least 8 characters", "pw_upper": "One uppercase letter",
        "pw_lower": "One lowercase letter", "pw_digit": "One digit",
        "pw_special": "One special character (! ? # $ ...)",
        "hero_title": "A real flight reservation in minutes",
        "hero_sub": "A <b>genuine airline reservation (PNR)</b> without buying"
                    " the ticket — verifiable on the airline's website, delivered"
                    " to your e-mail with a printable PDF itinerary. Perfect for"
                    " <b>visa applications</b> and <b>proof of onward travel</b>.",
        "badge1": "Real, verifiable PNR", "badge2": "Delivered in minutes",
        "badge3": "PDF itinerary + QR verification",
        "order_title": "Order your reservation",
        "book_need_account_text": "Reservations are placed from your account — it "
            "keeps your booking history and lets you reuse traveller details. "
            "Creating one takes a few seconds.",
        "book_register_btn": "Create account & book",
        "book_signin_btn": "I already have an account",
        "validity": "Validity",
        "plan_basic": "Standard",
        "plan_basic_desc": "One reservation, valid 24–72 h (airline dependent)",
        "plan_week": "7 days",
        "plan_week_desc": "Auto-renewed with a fresh PNR whenever it expires —"
                          " kept valid for 7 days",
        "plan_2week": "14 days",
        "plan_2week_desc": "Auto-renewed for 14 days — ideal for longer visa"
                           " processing",
        "trip_type": "Trip type",
        "oneway": "One way", "oneway_desc": "Single flight",
        "round": "Round trip", "round_desc": "There and back",
        "multi": "Multi-city", "multi_desc": "2–3 flights",
        "from": "From", "to": "To", "depart": "Departure date",
        "return": "Return date", "flight2": "Flight 2",
        "flight3": "Flight 3 (optional)", "date": "Date",
        "placeholder_city": "City or airport",
        "email": "E-mail (itinerary is sent here)",
        "phone": "Phone (international, +34...)",
        "passenger": "Passenger", "title_lbl": "Title",
        "given": "Given name (as in passport)",
        "surname": "Surname (as in passport)",
        "dob": "Date of birth", "gender": "Gender",
        "male": "Male", "female": "Female",
        "add_passenger": "+ Add passenger",
        "pay_method": "Payment method",
        "pay_card": "Card", "pay_card_desc": "Visa, Mastercard — via Stripe",
        "pay_crypto": "Crypto",
        "pay_crypto_desc": "BTC, XMR, ZEC, ETH, USDT — 300+ coins",
        "submit": "Get my reservation",
        "fee_note": "You pay only our service fee. We never charge you the price"
                    " of the flight and the airline is never paid.",
        "how_title": "How it works",
        "how1": "You pay the service fee — nothing else, ever.",
        "how2": "We place a real reservation with the airline in your name —"
                " a booking with a PNR code, held without payment.",
        "how3": "The itinerary with the PNR and a printable PDF arrives in your"
                " inbox, usually within minutes. Verify it on the airline's own"
                " website (“Manage booking”).",
        "how4": "Standard: the airline releases the unpaid booking after"
                " 24–72 hours. With the 7/14-day option we automatically create"
                " a fresh reservation each time one expires and e-mail you the"
                " new PNR.",
        "what_title": "What it is — and what it is not",
        "what_html": "<p>You receive a <b>real reservation</b>, not an edited"
                     " PDF: the PNR exists in the airline's system and anyone"
                     " can verify it while it is valid.</p><p>It is <b>not a"
                     " flight ticket</b> — you cannot board with it, and once"
                     " it expires, verification will show it as released."
                     " Embassies commonly accept (and often recommend)"
                     " unticketed reservations for visa applications; the"
                     " auto-renew options keep a live PNR in your inbox for the"
                     " whole processing window.</p>",
        "more_faq": "More questions? See the <a href='/faq'>FAQ</a>.",
        "footer": "provides unticketed flight reservations and cancellable hotel"
                  " reservations for visa applications and proof of onward"
                  " travel. A reservation is not a flight ticket or a paid stay"
                  " and cannot be used to board.",
        "st_confirmed": "Reservation confirmed",
        "st_passengers": "Passengers",
        "th_flight": "Flight", "th_route": "Route",
        "th_dep": "Departure", "th_arr": "Arrival",
        "st_valid": "Valid until",
        "st_verify": "Verify it on the airline's website under “Manage"
                     " booking” with the PNR and your surname. The itinerary"
                     " was also sent to",
        "st_autorenew": "Auto-renew is on: whenever the airline releases this"
                        " hold, we create a fresh reservation and e-mail you"
                        " the new PNR — until",
        "st_renewed": "Renewed", "st_renewed_sofar": "x so far.",
        "st_download": "Download PDF itinerary",
        "st_working": "Working on it...",
        "st_working_text": "Your reservation is being created. This page"
                           " refreshes automatically; the itinerary will also"
                           " arrive by e-mail.",
        "st_expired": "Reservation expired",
        "st_expired_text": "reached the end of its validity and was released by"
                           " the airline. Need a fresh one?",
        "st_new_order": "Place a new order",
        "st_failed": "We could not complete this reservation",
        "st_failed_text": "If you already paid, we will make it right or refund"
                          " you in full. Questions:",
        "back": "Back",
        "faq_title": "Frequently asked questions",
        "faq_html": """
<div class="card"><h2>Is the reservation real?</h2><p>Yes. We create an actual
booking in the airline's reservation system — the same kind a travel agency
creates before ticketing. It has a real PNR code you can verify on the
airline's website under “Manage booking” (PNR + passenger surname) for as long
as it is valid.</p></div>
<div class="card"><h2>Can I fly with it?</h2><p><b>No.</b> A reservation is not
a ticket — no ticket number is issued and it cannot be used to board. It is
supporting documentation for a visa application or proof of onward
travel.</p></div>
<div class="card"><h2>How long is it valid?</h2><p>The airline holds an unpaid
booking for 24–72 hours, depending on the carrier. With the 7-day or 14-day
option we automatically create a fresh reservation each time one is released
and e-mail you the new PNR, so you have a live, verifiable booking for the
whole period.</p></div>
<div class="card"><h2>Do embassies accept it?</h2><p>Most embassies ask for a
flight <i>reservation or itinerary</i> — many explicitly advise <b>not</b> to
buy a ticket before the visa is approved. An unticketed reservation is the
standard document for this purpose. Always check your embassy's exact
requirements; time your appointment so the reservation is valid on the day it
is checked (or use auto-renew).</p></div>
<div class="card"><h2>How fast will I get it?</h2><p>Usually within minutes of
payment. If no hold-capable fare exists for your route and date, we'll tell
you right away and refund you in full.</p></div>
<div class="card"><h2>What is your refund policy?</h2><p>If we cannot deliver
a verifiable reservation, you get a full refund — no questions asked. See
<a href="/terms">Terms</a>.</p></div>""",
    },
    "es": {
        "pw_hint": "Al menos 10 caracteres. También comprobamos que no haya aparecido en una filtración de datos conocida.",
        "google_btn": "Continuar con Google", "or": "o",
        "link_btn": "Enviarme un enlace de acceso",
        "link_note": "Sin contraseña: enviamos un enlace de un solo uso, válido 30 minutos.",
        "link_sent": "Si existe una cuenta con ese e-mail, el enlace de acceso va en camino.",
        "link_confirm_text": "Pulsa el botón para terminar de iniciar sesión en este dispositivo.",
        "link_confirm_btn": "Entrar", "password_login": "Entrar con contraseña",
        "register_optional": "La cuenta es opcional: también puedes reservar sin ella y entrar"
            " más tarde con un enlace por e-mail.",
        "guest_order_text": "No necesitas cuenta: la creamos automáticamente con tu e-mail y"
            " puedes entrar cuando quieras con un enlace de un solo uso. ¿Ya tienes cuenta?",
        "needed_on_lbl": "Fecha de la cita en la embajada o del check-in (opcional)",
        "needed_on_note": "Indícanos cuándo debe ser válida la reserva y la crearemos la noche"
            " anterior, para que esté activa ese día.",
        "calc_basic": "Crearemos tu reserva la noche anterior a esta fecha y te la enviaremos"
            " al momento: será válida ese día.",
        "calc_week": "", "calc_twoweek": "Faltan más de 60 días: reserva más cerca de la fecha"
            " o elige el plan de 14 días si la necesitas ya.",
        "sample_btn": "Ver un documento de ejemplo (PDF)",
        "hotel_soon_title": "Las reservas de hotel llegarán pronto.",
        "hotel_soon_text": "Estamos conectando a nuestros socios hoteleros. Las reservas de"
            " vuelo ya están disponibles.",
        "residency_lbl": "Nacionalidad del huésped (país del pasaporte, 2 letras)",
        "residency_note": "Los hoteles fijan tarifas según el país del huésped, p. ej. ES, MX, CO.",
        "st_scheduled": "Pago recibido: reserva programada",
        "st_scheduled_text": "Para que tu reserva sea válida en tu fecha, la crearemos y te"
            " enviaremos el itinerario el",
        "nav_privacy": "Privacidad",
        "meta_title": "reservas de vuelo y hotel para visados",
        "meta_description": "Reservas de vuelo sin billete (PNR) y reservas de hotel"
            " cancelables para solicitudes de visado y prueba de salida, enviadas por"
            " e-mail con un PDF imprimible.",
        "test_title": "MODO DE PRUEBA.",
        "test_text": "Las reservas creadas en este sitio son por ahora reservas"
            " ficticias de prueba: no existen en el sistema de ninguna aerolínea ni"
            " hotel, no se pueden verificar y NO deben usarse para solicitar un"
            " visado. No se cobra ningún pago.",
        "operated_by": "Operado por", "company_id": "IČO", "tax_id": "DIČ",
        "vat_id": "IVA",
        "vat_note": "Precios con IVA incluido.",
        "consent_html": "Solicito que el servicio comience de inmediato y acepto que"
            " pierdo mi derecho de desistimiento una vez entregada la reserva. Acepto"
            " los <a href='/terms'>Términos</a> y he leído la"
            " <a href='/privacy'>Política de privacidad</a>.",
        "hotel_badge1": "Reserva real y cancelable",
        "hotel_badge3": "Bono PDF + QR",
        "hotel_price_note": "por reserva, sin importar el número de noches.",
        "hotel_what_html": "<p>Recibes una <b>reserva de hotel real y cancelable</b>"
            " con código de reserva — con tarifa de cancelación gratuita y liberada"
            " automáticamente antes del plazo de cancelación. Es documentación de"
            " apoyo para visados y prueba de alojamiento, <b>no una estancia"
            " pagada</b>.</p>",
        "st_verify_short": "Verifícala en la web de la aerolínea en “Gestionar"
            " reserva” con el PNR y los apellidos del pasajero.",
        "st_sent_to": "Los documentos también se enviaron a",
        "st_test_confirmed": "Reserva de PRUEBA — no válida, no verificable",
        "st_refunded": "Reserva cancelada",
        "st_refunded_text": "El pago de esta reserva fue reembolsado o impugnado, por lo"
            " que la reserva se canceló y no se renovará.",
        "hotel_released": "fue liberada antes del plazo de cancelación gratuita.",
        "nav_order": "Reservar", "nav_faq": "FAQ", "nav_terms": "Términos",
        "nav_login": "Entrar", "nav_account": "Mi cuenta", "nav_logout": "Salir",
        "nav_hotel": "Hotel",
        "hotel_hero_title": "Una reserva de hotel real para tu visado",
        "hotel_hero_sub": "Una <b>reserva de hotel genuina y cancelable</b> con"
            " número de confirmación — con tarifa de cancelación gratuita y"
            " enviada en PDF. Perfecta para <b>solicitudes de visado</b> y"
            " <b>prueba de alojamiento</b>.",
        "hotel_order_title": "Pide tu reserva de hotel",
        "city_lbl": "Ciudad de destino", "checkin_lbl": "Entrada",
        "checkout_lbl": "Salida", "guest": "Huésped", "add_guest": "+ Añadir huésped",
        "hotel_submit": "Obtener mi reserva de hotel",
        "hotel_confirmed": "Reserva de hotel confirmada",
        "hotel_download": "Descargar reserva PDF",
        "checkin_th": "Entrada", "checkout_th": "Salida", "hotel_th": "Hotel",
        "login_title": "Iniciar sesión", "register_title": "Crear una cuenta",
        "email_lbl": "E-mail", "password_lbl": "Contraseña", "min8": "mín. 8 caracteres",
        "login_btn": "Entrar", "register_btn": "Crear cuenta",
        "no_account": "¿Aún no tienes cuenta?", "have_account": "¿Ya tienes cuenta?",
        "forgot_link": "¿Olvidaste tu contraseña?",
        "forgot_title": "Restablecer contraseña",
        "forgot_text": "Introduce el e-mail de tu cuenta y te enviaremos un enlace.",
        "forgot_btn": "Enviar enlace",
        "forgot_sent": "Si existe una cuenta con ese e-mail, el enlace va en camino.",
        "reset_title": "Nueva contraseña", "new_password": "Nueva contraseña",
        "reset_btn": "Cambiar contraseña",
        "account_title": "Mi cuenta", "order_history": "Historial de pedidos",
        "th_date": "Fecha", "th_status": "Estado", "view": "Ver",
        "no_orders": "Aún no hay pedidos.",
        "saved_passengers": "Viajeros guardados",
        "saved_passengers_note": "Guarda los datos del viajero para reutilizarlos"
            " en futuros pedidos. Los datos del pasaporte son opcionales y se"
            " guardan cifrados.",
        "nationality": "Nacionalidad", "passport": "Número de pasaporte",
        "passport_expiry": "Caducidad del pasaporte",
        "add_saved_passenger": "Añadir viajero",
        "passport_note": "Opcional. Se guarda cifrado; se usa solo para completar"
            " reservas internacionales.",
        "delete": "Eliminar", "save": "Guardar",
        "new_order_btn": "Nueva reserva", "traveller_saved": "Viajero guardado.",
        "pw_len": "Al menos 8 caracteres", "pw_upper": "Una mayúscula",
        "pw_lower": "Una minúscula", "pw_digit": "Un número",
        "pw_special": "Un carácter especial (! ? # $ ...)",
        "hero_title": "Una reserva de vuelo real en minutos",
        "hero_sub": "Una <b>reserva aérea genuina (PNR)</b> sin comprar el"
                    " billete — verificable en la web de la aerolínea, enviada"
                    " a tu correo con un itinerario PDF imprimible. Perfecta"
                    " para <b>solicitudes de visado</b> y <b>prueba de vuelo de"
                    " salida</b> (onward travel).",
        "badge1": "PNR real y verificable", "badge2": "Entrega en minutos",
        "badge3": "Itinerario PDF + verificación QR",
        "order_title": "Pide tu reserva",
        "book_need_account_text": "Las reservas se hacen desde tu cuenta — guarda "
            "tu historial y te permite reutilizar los datos de los pasajeros. "
            "Crear una cuenta lleva unos segundos.",
        "book_register_btn": "Crear cuenta y reservar",
        "book_signin_btn": "Ya tengo una cuenta",
        "validity": "Validez",
        "plan_basic": "Estándar",
        "plan_basic_desc": "Una reserva, válida 24–72 h (según la aerolínea)",
        "plan_week": "7 días",
        "plan_week_desc": "Renovada automáticamente con un PNR nuevo cada vez"
                          " que expira — válida durante 7 días",
        "plan_2week": "14 días",
        "plan_2week_desc": "Renovación automática durante 14 días — ideal para"
                           " trámites de visado largos",
        "trip_type": "Tipo de viaje",
        "oneway": "Solo ida", "oneway_desc": "Un vuelo",
        "round": "Ida y vuelta", "round_desc": "Ida y regreso",
        "multi": "Multidestino", "multi_desc": "2–3 vuelos",
        "from": "Origen", "to": "Destino", "depart": "Fecha de salida",
        "return": "Fecha de regreso", "flight2": "Vuelo 2",
        "flight3": "Vuelo 3 (opcional)", "date": "Fecha",
        "placeholder_city": "Ciudad o aeropuerto",
        "email": "E-mail (el itinerario se envía aquí)",
        "phone": "Teléfono (internacional, +34...)",
        "passenger": "Pasajero", "title_lbl": "Tratamiento",
        "given": "Nombre (como en el pasaporte)",
        "surname": "Apellidos (como en el pasaporte)",
        "dob": "Fecha de nacimiento", "gender": "Sexo",
        "male": "Hombre", "female": "Mujer",
        "add_passenger": "+ Añadir pasajero",
        "pay_method": "Método de pago",
        "pay_card": "Tarjeta", "pay_card_desc": "Visa, Mastercard — vía Stripe",
        "pay_crypto": "Cripto",
        "pay_crypto_desc": "BTC, XMR, ZEC, ETH, USDT — 300+ monedas",
        "submit": "Obtener mi reserva",
        "fee_note": "Solo pagas nuestra tarifa de servicio. Nunca te cobramos"
                    " el precio del vuelo y la aerolínea nunca recibe pago.",
        "how_title": "Cómo funciona",
        "how1": "Pagas la tarifa del servicio — nada más, nunca.",
        "how2": "Creamos una reserva real con la aerolínea a tu nombre — una"
                " reserva con código PNR, retenida sin pago.",
        "how3": "El itinerario con el PNR y un PDF imprimible llega a tu"
                " correo, normalmente en minutos. Verifícalo en la propia web"
                " de la aerolínea (“Gestionar reserva”).",
        "how4": "Estándar: la aerolínea libera la reserva no pagada tras"
                " 24–72 horas. Con la opción de 7/14 días creamos"
                " automáticamente una reserva nueva cada vez que expira y te"
                " enviamos el nuevo PNR.",
        "what_title": "Qué es — y qué no es",
        "what_html": "<p>Recibes una <b>reserva real</b>, no un PDF editado:"
                     " el PNR existe en el sistema de la aerolínea y cualquiera"
                     " puede verificarlo mientras es válido.</p><p><b>No es un"
                     " billete de avión</b> — no puedes embarcar con ella y,"
                     " una vez expirada, la verificación la mostrará como"
                     " liberada. Las embajadas aceptan habitualmente (y a"
                     " menudo recomiendan) reservas sin emitir para solicitudes"
                     " de visado; las opciones de renovación automática"
                     " mantienen un PNR activo durante todo el trámite.</p>",
        "more_faq": "¿Más preguntas? Consulta las <a href='/faq'>FAQ</a>.",
        "footer": "ofrece reservas de vuelo sin billete y reservas de hotel"
                  " cancelables para solicitudes de visado y prueba de salida."
                  " Una reserva no es un billete ni una estancia pagada y no"
                  " permite embarcar.",
        "st_confirmed": "Reserva confirmada",
        "st_passengers": "Pasajeros",
        "th_flight": "Vuelo", "th_route": "Ruta",
        "th_dep": "Salida", "th_arr": "Llegada",
        "st_valid": "Válida hasta",
        "st_verify": "Verifícala en la web de la aerolínea en “Gestionar"
                     " reserva” con el PNR y tus apellidos. El itinerario"
                     " también se envió a",
        "st_autorenew": "Renovación automática activada: cada vez que la"
                        " aerolínea libere esta reserva, crearemos una nueva y"
                        " te enviaremos el nuevo PNR — hasta el",
        "st_renewed": "Renovada", "st_renewed_sofar": "x hasta ahora.",
        "st_download": "Descargar itinerario PDF",
        "st_working": "Procesando...",
        "st_working_text": "Tu reserva se está creando. Esta página se"
                           " actualiza sola; el itinerario también llegará por"
                           " e-mail.",
        "st_expired": "Reserva expirada",
        "st_expired_text": "llegó al final de su validez y fue liberada por la"
                           " aerolínea. ¿Necesitas una nueva?",
        "st_new_order": "Haz un nuevo pedido",
        "st_failed": "No pudimos completar esta reserva",
        "st_failed_text": "Si ya pagaste, lo solucionaremos o te devolveremos"
                          " el importe completo. Consultas:",
        "back": "Volver",
        "faq_title": "Preguntas frecuentes",
        "faq_html": """
<div class="card"><h2>¿La reserva es real?</h2><p>Sí. Creamos una reserva real
en el sistema de la aerolínea — la misma que crea una agencia de viajes antes
de emitir el billete. Tiene un código PNR real que puedes verificar en la web
de la aerolínea en “Gestionar reserva” (PNR + apellidos) mientras sea
válida.</p></div>
<div class="card"><h2>¿Puedo volar con ella?</h2><p><b>No.</b> Una reserva no
es un billete — no se emite número de billete y no permite embarcar. Es
documentación de apoyo para un visado o como prueba de vuelo de
salida.</p></div>
<div class="card"><h2>¿Cuánto dura su validez?</h2><p>La aerolínea mantiene una
reserva no pagada entre 24 y 72 horas, según la compañía. Con la opción de 7 o
14 días creamos automáticamente una reserva nueva cada vez que se libera y te
enviamos el nuevo PNR, de modo que tienes una reserva viva y verificable todo
el periodo.</p></div>
<div class="card"><h2>¿Las embajadas la aceptan?</h2><p>La mayoría de embajadas
piden una <i>reserva o itinerario</i> de vuelo — muchas incluso aconsejan
<b>no</b> comprar el billete antes de la aprobación del visado. Una reserva
sin emitir es el documento estándar para este fin. Comprueba siempre los
requisitos exactos de tu embajada y procura que la reserva esté activa el día
de la revisión (o usa la renovación automática).</p></div>
<div class="card"><h2>¿Cuándo la recibiré?</h2><p>Normalmente a los pocos
minutos del pago. Si no existe tarifa reservable para tu ruta y fecha, te lo
diremos de inmediato y te devolveremos el importe completo.</p></div>
<div class="card"><h2>¿Cuál es la política de reembolso?</h2><p>Si no podemos
entregar una reserva verificable, reembolso completo — sin preguntas. Ver
<a href="/terms">Términos</a>.</p></div>""",
    },
    "fr": {
        "pw_hint": "Au moins 10 caractères. Nous vérifions aussi qu'il n'apparaît dans"
            " aucune fuite de données connue.",
        "google_btn": "Continuer avec Google", "or": "ou",
        "link_btn": "M'envoyer un lien de connexion par e-mail",
        "link_note": "Aucun mot de passe requis : nous envoyons un lien à usage unique,"
            " valable 30 minutes.",
        "link_sent": "Si un compte existe pour cet e-mail, un lien de connexion est en route.",
        "link_confirm_text": "Cliquez sur le bouton pour terminer la connexion sur cet appareil.",
        "link_confirm_btn": "Se connecter",
        "password_login": "Se connecter plutôt avec un mot de passe",
        "register_optional": "Le compte est facultatif : vous pouvez aussi commander sans"
            " compte et vous connecter plus tard avec un lien envoyé par e-mail.",
        "guest_order_text": "Aucun compte nécessaire : nous en créons un automatiquement pour"
            " votre e-mail et vous pouvez vous connecter à tout moment avec un lien à usage"
            " unique envoyé par e-mail. Vous avez déjà un compte ?",
        "needed_on_lbl": "Date du rendez-vous à l'ambassade ou de l'enregistrement (facultatif)",
        "needed_on_note": "Indiquez-nous quand la réservation doit être valable : nous la"
            " créerons la veille au soir, pour qu'elle soit active ce jour-là.",
        "calc_basic": "Nous créerons votre réservation la veille au soir de cette date et"
            " vous l'enverrons aussitôt par e-mail — elle sera valable le jour même.",
        "calc_week": "", "calc_twoweek": "Plus de 60 jours à l'avance — commandez plus près"
            " de la date, ou choisissez la formule 14 jours si vous en avez besoin maintenant.",
        "sample_btn": "Voir un exemple de document (PDF)",
        "hotel_soon_title": "Les réservations d'hôtel arrivent bientôt.",
        "hotel_soon_text": "Nous connectons nos partenaires de réservation hôtelière. Les"
            " réservations de vol sont disponibles dès maintenant.",
        "residency_lbl": "Nationalité du client (pays du passeport, 2 lettres)",
        "residency_note": "Les hôtels fixent leurs tarifs selon le pays du client,"
            " p. ex. SK, DE, IN.",
        "st_scheduled": "Paiement reçu — réservation programmée",
        "st_scheduled_text": "Pour que votre réservation soit valable à votre date, nous la"
            " créerons et vous enverrons l'itinéraire par e-mail le",
        "nav_privacy": "Confidentialité",
        "meta_title": "réservations de vol et d'hôtel pour les demandes de visa",
        "meta_description": "Réservations de vol sans billet (PNR) et réservations d'hôtel"
            " annulables pour les demandes de visa et la preuve de voyage de sortie,"
            " envoyées par e-mail avec un PDF imprimable.",
        "test_title": "MODE TEST.",
        "test_text": "Les réservations créées sur ce site sont actuellement des"
            " réservations fictives de test : elles n'existent dans le système d'aucune"
            " compagnie aérienne ni d'aucun hôtel, ne peuvent pas être vérifiées et ne"
            " doivent PAS être utilisées pour une demande de visa. Aucun paiement n'est"
            " prélevé.",
        "operated_by": "Exploité par", "company_id": "N° d'entreprise",
        "tax_id": "N° fiscal", "vat_id": "N° de TVA",
        "vat_note": "Prix TTC (TVA incluse).",
        "consent_html": "Je demande que le service commence immédiatement et je reconnais"
            " perdre mon droit de rétractation dès que la réservation a été livrée."
            " J'accepte les <a href='/terms'>Conditions</a> et j'ai lu la"
            " <a href='/privacy'>Politique de confidentialité</a>.",
        "hotel_badge1": "Réservation réelle et annulable",
        "hotel_badge3": "Voucher PDF + QR",
        "hotel_price_note": "par réservation, quel que soit le nombre de nuits.",
        "hotel_what_html": "<p>Vous recevez une <b>réservation d'hôtel réelle et"
            " annulable</b> avec une référence de réservation — maintenue sur un tarif à"
            " annulation gratuite et libérée automatiquement avant la date limite"
            " d'annulation. C'est un justificatif pour les demandes de visa et une preuve"
            " d'hébergement, <b>pas un séjour payé</b>.</p>",
        "st_verify_short": "Vérifiez-la sur le site de la compagnie aérienne, rubrique"
            " « Gérer ma réservation », avec le PNR et le nom de famille du passager.",
        "st_sent_to": "Les documents ont également été envoyés à",
        "st_test_confirmed": "Réservation de TEST — non valable, non vérifiable",
        "st_refunded": "Réservation annulée",
        "st_refunded_text": "Le paiement de cette réservation a été remboursé ou contesté ;"
            " la réservation a donc été annulée et ne sera pas renouvelée.",
        "hotel_released": "a été libérée avant la date limite d'annulation gratuite.",
        "nav_order": "Commander", "nav_faq": "FAQ", "nav_terms": "Conditions",
        "nav_login": "Connexion", "nav_account": "Mon compte", "nav_logout": "Déconnexion",
        "nav_hotel": "Hôtel",
        "hotel_hero_title": "Une vraie réservation d'hôtel pour votre visa",
        "hotel_hero_sub": "Une <b>réservation d'hôtel authentique et annulable</b> avec un"
            " numéro de confirmation — maintenue sur un tarif à annulation gratuite et"
            " livrée en PDF imprimable. Idéale pour les <b>demandes de visa</b> et la"
            " <b>preuve d'hébergement</b>.",
        "hotel_order_title": "Commandez votre réservation d'hôtel",
        "city_lbl": "Ville de destination", "checkin_lbl": "Arrivée",
        "checkout_lbl": "Départ", "guest": "Client", "add_guest": "+ Ajouter un client",
        "hotel_submit": "Obtenir ma réservation d'hôtel",
        "hotel_confirmed": "Réservation d'hôtel confirmée",
        "hotel_download": "Télécharger la réservation PDF",
        "checkin_th": "Arrivée", "checkout_th": "Départ", "hotel_th": "Hôtel",
        "login_title": "Connexion", "register_title": "Créer un compte",
        "email_lbl": "E-mail", "password_lbl": "Mot de passe", "min8": "8 caractères min.",
        "login_btn": "Se connecter", "register_btn": "Créer un compte",
        "no_account": "Pas encore de compte ?", "have_account": "Vous avez déjà un compte ?",
        "forgot_link": "Mot de passe oublié ?",
        "forgot_title": "Réinitialiser votre mot de passe",
        "forgot_text": "Saisissez l'e-mail de votre compte et nous vous enverrons un lien"
            " de réinitialisation.",
        "forgot_btn": "Envoyer le lien de réinitialisation",
        "forgot_sent": "Si un compte existe pour cet e-mail, un lien de réinitialisation"
            " est en route.",
        "reset_title": "Définir un nouveau mot de passe",
        "new_password": "Nouveau mot de passe",
        "reset_btn": "Changer le mot de passe",
        "account_title": "Mon compte", "order_history": "Historique des commandes",
        "th_date": "Date", "th_status": "Statut", "view": "Voir",
        "no_orders": "Aucune commande pour l'instant.",
        "saved_passengers": "Voyageurs enregistrés",
        "saved_passengers_note": "Enregistrez les informations des voyageurs pour les"
            " réutiliser lors de vos prochaines commandes. Les données du passeport sont"
            " facultatives et stockées chiffrées.",
        "nationality": "Nationalité", "passport": "Numéro de passeport",
        "passport_expiry": "Expiration du passeport",
        "add_saved_passenger": "Ajouter un voyageur",
        "passport_note": "Facultatif. Stocké chiffré ; utilisé uniquement pour finaliser"
            " les réservations internationales.",
        "delete": "Supprimer", "save": "Enregistrer",
        "new_order_btn": "Nouvelle réservation", "traveller_saved": "Voyageur enregistré.",
        "pw_len": "Au moins 8 caractères", "pw_upper": "Une lettre majuscule",
        "pw_lower": "Une lettre minuscule", "pw_digit": "Un chiffre",
        "pw_special": "Un caractère spécial (! ? # $ ...)",
        "hero_title": "Une vraie réservation de vol en quelques minutes",
        "hero_sub": "Une <b>réservation aérienne authentique (PNR)</b> sans acheter"
                    " le billet — vérifiable sur le site de la compagnie aérienne,"
                    " envoyée à votre e-mail avec un itinéraire PDF imprimable. Idéale"
                    " pour les <b>demandes de visa</b> et la <b>preuve de voyage de"
                    " sortie</b>.",
        "badge1": "PNR réel et vérifiable", "badge2": "Livré en quelques minutes",
        "badge3": "Itinéraire PDF + vérification QR",
        "order_title": "Commandez votre réservation",
        "book_need_account_text": "Les réservations se font depuis votre compte — il "
            "conserve l'historique de vos réservations et vous permet de réutiliser les "
            "informations des voyageurs. La création ne prend que quelques secondes.",
        "book_register_btn": "Créer un compte et réserver",
        "book_signin_btn": "J'ai déjà un compte",
        "validity": "Validité",
        "plan_basic": "Standard",
        "plan_basic_desc": "Une réservation, valable 24 à 72 h (selon la compagnie)",
        "plan_week": "7 jours",
        "plan_week_desc": "Renouvelée automatiquement avec un nouveau PNR à chaque"
                          " expiration — maintenue valable pendant 7 jours",
        "plan_2week": "14 jours",
        "plan_2week_desc": "Renouvellement automatique pendant 14 jours — idéal pour"
                           " les traitements de visa plus longs",
        "trip_type": "Type de voyage",
        "oneway": "Aller simple", "oneway_desc": "Un seul vol",
        "round": "Aller-retour", "round_desc": "Aller et retour",
        "multi": "Multi-destinations", "multi_desc": "2 à 3 vols",
        "from": "Départ", "to": "Arrivée", "depart": "Date de départ",
        "return": "Date de retour", "flight2": "Vol 2",
        "flight3": "Vol 3 (facultatif)", "date": "Date",
        "placeholder_city": "Ville ou aéroport",
        "email": "E-mail (l'itinéraire est envoyé ici)",
        "phone": "Téléphone (format international, +34...)",
        "passenger": "Passager", "title_lbl": "Civilité",
        "given": "Prénom (comme sur le passeport)",
        "surname": "Nom (comme sur le passeport)",
        "dob": "Date de naissance", "gender": "Sexe",
        "male": "Homme", "female": "Femme",
        "add_passenger": "+ Ajouter un passager",
        "pay_method": "Moyen de paiement",
        "pay_card": "Carte", "pay_card_desc": "Visa, Mastercard — via Stripe",
        "pay_crypto": "Crypto",
        "pay_crypto_desc": "BTC, XMR, ZEC, ETH, USDT — plus de 300 cryptomonnaies",
        "submit": "Obtenir ma réservation",
        "fee_note": "Vous ne payez que nos frais de service. Nous ne vous facturons"
                    " jamais le prix du vol et la compagnie aérienne n'est jamais payée.",
        "how_title": "Comment ça marche",
        "how1": "Vous payez les frais de service — rien d'autre, jamais.",
        "how2": "Nous effectuons une vraie réservation auprès de la compagnie aérienne"
                " à votre nom — une réservation avec un code PNR, maintenue sans paiement.",
        "how3": "L'itinéraire avec le PNR et un PDF imprimable arrive dans votre boîte"
                " de réception, généralement en quelques minutes. Vérifiez-le sur le site"
                " de la compagnie aérienne elle-même (« Gérer ma réservation »).",
        "how4": "Standard : la compagnie aérienne libère la réservation non payée après"
                " 24 à 72 heures. Avec l'option 7/14 jours, nous créons automatiquement"
                " une nouvelle réservation à chaque expiration et vous envoyons le"
                " nouveau PNR par e-mail.",
        "what_title": "Ce que c'est — et ce que ce n'est pas",
        "what_html": "<p>Vous recevez une <b>vraie réservation</b>, pas un PDF"
                     " retouché : le PNR existe dans le système de la compagnie"
                     " aérienne et chacun peut le vérifier tant qu'il est valable.</p>"
                     "<p>Ce n'est <b>pas un billet d'avion</b> — vous ne pouvez pas"
                     " embarquer avec, et une fois expirée, la vérification l'indiquera"
                     " comme libérée. Les ambassades acceptent couramment (et"
                     " recommandent souvent) les réservations sans billet pour les"
                     " demandes de visa ; les options de renouvellement automatique"
                     " maintiennent un PNR actif dans votre boîte de réception pendant"
                     " toute la durée du traitement.</p>",
        "more_faq": "D'autres questions ? Consultez la <a href='/faq'>FAQ</a>.",
        "footer": "propose des réservations de vol sans billet et des réservations"
                  " d'hôtel annulables pour les demandes de visa et la preuve de voyage"
                  " de sortie. Une réservation n'est ni un billet d'avion ni un séjour"
                  " payé et ne permet pas d'embarquer.",
        "st_confirmed": "Réservation confirmée",
        "st_passengers": "Passagers",
        "th_flight": "Vol", "th_route": "Trajet",
        "th_dep": "Départ", "th_arr": "Arrivée",
        "st_valid": "Valable jusqu'au",
        "st_verify": "Vérifiez-la sur le site de la compagnie aérienne, rubrique"
                     " « Gérer ma réservation », avec le PNR et votre nom de famille."
                     " L'itinéraire a également été envoyé à",
        "st_autorenew": "Renouvellement automatique activé : chaque fois que la"
                        " compagnie libère cette réservation, nous en créons une"
                        " nouvelle et vous envoyons le nouveau PNR par e-mail —"
                        " jusqu'au",
        "st_renewed": "Renouvelée", "st_renewed_sofar": " fois jusqu'à présent.",
        "st_download": "Télécharger l'itinéraire PDF",
        "st_working": "Traitement en cours...",
        "st_working_text": "Votre réservation est en cours de création. Cette page"
                           " s'actualise automatiquement ; l'itinéraire arrivera"
                           " aussi par e-mail.",
        "st_expired": "Réservation expirée",
        "st_expired_text": "est arrivée en fin de validité et a été libérée par la"
                           " compagnie aérienne. Besoin d'une nouvelle ?",
        "st_new_order": "Passer une nouvelle commande",
        "st_failed": "Nous n'avons pas pu finaliser cette réservation",
        "st_failed_text": "Si vous avez déjà payé, nous trouverons une solution ou vous"
                          " rembourserons intégralement. Questions :",
        "back": "Retour",
        "faq_title": "Questions fréquentes",
        "faq_html": """
<div class="card"><h2>La réservation est-elle réelle ?</h2><p>Oui. Nous créons une
véritable réservation dans le système de réservation de la compagnie aérienne — du
même type que celle qu'une agence de voyages crée avant l'émission du billet. Elle
possède un vrai code PNR que vous pouvez vérifier sur le site de la compagnie,
rubrique « Gérer ma réservation » (PNR + nom du passager), tant qu'elle est
valable.</p></div>
<div class="card"><h2>Puis-je voyager avec ?</h2><p><b>Non.</b> Une réservation
n'est pas un billet — aucun numéro de billet n'est émis et elle ne permet pas
d'embarquer. C'est un justificatif pour une demande de visa ou une preuve de voyage
de sortie.</p></div>
<div class="card"><h2>Combien de temps est-elle valable ?</h2><p>La compagnie
aérienne conserve une réservation non payée pendant 24 à 72 heures, selon le
transporteur. Avec l'option 7 jours ou 14 jours, nous créons automatiquement une
nouvelle réservation à chaque libération et vous envoyons le nouveau PNR par
e-mail, afin que vous disposiez d'une réservation active et vérifiable pendant toute
la période.</p></div>
<div class="card"><h2>Les ambassades l'acceptent-elles ?</h2><p>La plupart des
ambassades demandent une <i>réservation ou un itinéraire</i> de vol — beaucoup
conseillent explicitement de <b>ne pas</b> acheter de billet avant l'approbation du
visa. Une réservation sans billet est le document standard à cet effet. Vérifiez
toujours les exigences exactes de votre ambassade ; planifiez votre rendez-vous pour
que la réservation soit valable le jour où elle est contrôlée (ou utilisez le
renouvellement automatique).</p></div>
<div class="card"><h2>En combien de temps vais-je la recevoir ?</h2><p>Généralement
quelques minutes après le paiement. S'il n'existe aucun tarif permettant une
réservation sans paiement pour votre trajet et votre date, nous vous le dirons tout
de suite et vous rembourserons intégralement.</p></div>
<div class="card"><h2>Quelle est votre politique de remboursement ?</h2><p>Si nous
ne pouvons pas fournir une réservation vérifiable, vous êtes remboursé
intégralement — sans poser de questions. Voir les
<a href="/terms">Conditions</a>.</p></div>""",
    },
    "ar": {
        "pw_hint": "10 أحرف على الأقل. ونتحقق أيضاً من أنها لم تظهر في أي تسريب بيانات معروف.",
        "google_btn": "المتابعة باستخدام Google", "or": "أو",
        "link_btn": "أرسل لي رابط تسجيل الدخول بالبريد الإلكتروني",
        "link_note": "لا حاجة إلى كلمة مرور — نرسل رابطاً لمرة واحدة صالحاً لمدة 30 دقيقة.",
        "link_sent": "إذا كان هناك حساب مرتبط بهذا البريد الإلكتروني، فرابط تسجيل الدخول"
            " في الطريق إليك.",
        "link_confirm_text": "انقر على الزر لإكمال تسجيل الدخول على هذا الجهاز.",
        "link_confirm_btn": "تسجيل الدخول",
        "password_login": "تسجيل الدخول بكلمة مرور بدلاً من ذلك",
        "register_optional": "الحساب اختياري — يمكنك أيضاً الطلب دون حساب وتسجيل الدخول"
            " لاحقاً عبر رابط يُرسل إلى بريدك الإلكتروني.",
        "guest_order_text": "لا حاجة إلى حساب: ننشئ حساباً لبريدك الإلكتروني تلقائياً"
            " ويمكنك تسجيل الدخول في أي وقت عبر رابط لمرة واحدة يُرسل إلى بريدك"
            " الإلكتروني. هل لديك حساب بالفعل؟",
        "needed_on_lbl": "تاريخ موعد السفارة أو تاريخ تسجيل الوصول (اختياري)",
        "needed_on_note": "أخبرنا متى يجب أن يكون الحجز صالحاً، وسننشئه في مساء اليوم"
            " السابق ليكون سارياً في ذلك اليوم.",
        "calc_basic": "سننشئ حجزك في مساء اليوم السابق لهذا التاريخ ونرسله إلى بريدك"
            " الإلكتروني فوراً — وسيكون صالحاً في ذلك اليوم.",
        "calc_week": "", "calc_twoweek": "يفصلنا أكثر من 60 يوماً عن هذا التاريخ — اطلب"
            " في موعد أقرب إليه، أو اختر خطة 14 يوماً إذا كنت بحاجة إليه الآن.",
        "sample_btn": "عرض مستند نموذجي (PDF)",
        "hotel_soon_title": "حجوزات الفنادق قادمة قريباً.",
        "hotel_soon_text": "نعمل حالياً على ربط شركائنا في حجز الفنادق. حجوزات الطيران"
            " متاحة الآن.",
        "residency_lbl": "جنسية النزيل (بلد جواز السفر، حرفان)",
        "residency_note": "تحدد الفنادق أسعارها حسب بلد النزيل، مثل SK وDE وIN.",
        "st_scheduled": "تم استلام الدفعة — الحجز مجدول",
        "st_scheduled_text": "لكي يكون حجزك صالحاً في التاريخ المطلوب، سننشئه ونرسل خط"
            " سير الرحلة إلى بريدك الإلكتروني في",
        "nav_privacy": "الخصوصية",
        "meta_title": "حجوزات طيران وفنادق لطلبات التأشيرة",
        "meta_description": "حجوزات طيران دون إصدار تذكرة (PNR) وحجوزات فنادق قابلة للإلغاء"
            " لطلبات التأشيرة وإثبات مواصلة السفر، تُرسل بالبريد الإلكتروني مع ملف PDF"
            " قابل للطباعة.",
        "test_title": "وضع الاختبار.",
        "test_text": "الحجوزات التي تُنشأ على هذا الموقع حالياً حجوزات تجريبية وهمية:"
            " لا وجود لها في نظام أي شركة طيران أو فندق، ولا يمكن التحقق منها، ويجب"
            " عدم استخدامها إطلاقاً في طلب تأشيرة. لا يتم تحصيل أي مبلغ.",
        "operated_by": "يُدار بواسطة", "company_id": "رقم تسجيل الشركة",
        "tax_id": "الرقم الضريبي", "vat_id": "رقم ضريبة القيمة المضافة",
        "vat_note": "الأسعار تشمل ضريبة القيمة المضافة.",
        "consent_html": "أطلب أن تبدأ الخدمة فوراً، وأُقرّ بأنني أفقد حقي في الانسحاب"
            " (العدول) بمجرد تسليم الحجز. أوافق على <a href='/terms'>الشروط</a> وقد"
            " اطّلعت على <a href='/privacy'>سياسة الخصوصية</a>.",
        "hotel_badge1": "حجز حقيقي قابل للإلغاء",
        "hotel_badge3": "قسيمة PDF + رمز QR",
        "hotel_price_note": "لكل حجز، بغض النظر عن عدد الليالي.",
        "hotel_what_html": "<p>تحصل على <b>حجز فندقي حقيقي قابل للإلغاء</b> برقم مرجعي"
            " — محجوز بسعر يتيح الإلغاء المجاني ويُلغى تلقائياً قبل انتهاء مهلة الإلغاء."
            " وهو مستند داعم لطلبات التأشيرة وإثبات الإقامة، <b>وليس إقامة مدفوعة"
            "</b>.</p>",
        "st_verify_short": "تحقق منه على موقع شركة الطيران ضمن «إدارة الحجز» باستخدام"
            " رمز PNR واسم عائلة المسافر.",
        "st_sent_to": "أُرسلت المستندات أيضاً إلى",
        "st_test_confirmed": "حجز تجريبي — غير صالح ولا يمكن التحقق منه",
        "st_refunded": "تم إلغاء الحجز",
        "st_refunded_text": "تم استرداد مبلغ هذا الحجز أو الاعتراض عليه، ولذلك أُلغي"
            " الحجز ولن يُجدَّد.",
        "hotel_released": "أُلغي قبل انتهاء مهلة الإلغاء المجاني.",
        "nav_order": "اطلب", "nav_faq": "الأسئلة الشائعة", "nav_terms": "الشروط",
        "nav_login": "تسجيل الدخول", "nav_account": "حسابي", "nav_logout": "تسجيل الخروج",
        "nav_hotel": "فندق",
        "hotel_hero_title": "حجز فندقي حقيقي لتأشيرتك",
        "hotel_hero_sub": "<b>حجز فندقي أصلي قابل للإلغاء</b> برقم تأكيد — محجوز بسعر"
            " يتيح الإلغاء المجاني ويُرسل بصيغة PDF قابلة للطباعة. مثالي لـ<b>طلبات"
            " التأشيرة</b> و<b>إثبات الإقامة</b>.",
        "hotel_order_title": "اطلب حجزك الفندقي",
        "city_lbl": "مدينة الوجهة", "checkin_lbl": "تسجيل الوصول",
        "checkout_lbl": "تسجيل المغادرة", "guest": "النزيل", "add_guest": "+ إضافة نزيل",
        "hotel_submit": "احصل على حجزي الفندقي",
        "hotel_confirmed": "تم تأكيد الحجز الفندقي",
        "hotel_download": "تنزيل الحجز بصيغة PDF",
        "checkin_th": "الوصول", "checkout_th": "المغادرة", "hotel_th": "الفندق",
        "login_title": "تسجيل الدخول", "register_title": "إنشاء حساب",
        "email_lbl": "البريد الإلكتروني", "password_lbl": "كلمة المرور",
        "min8": "8 أحرف على الأقل",
        "login_btn": "تسجيل الدخول", "register_btn": "إنشاء حساب",
        "no_account": "ليس لديك حساب بعد؟", "have_account": "هل لديك حساب بالفعل؟",
        "forgot_link": "هل نسيت كلمة المرور؟",
        "forgot_title": "إعادة تعيين كلمة المرور",
        "forgot_text": "أدخل البريد الإلكتروني لحسابك وسنرسل إليك رابط إعادة التعيين.",
        "forgot_btn": "إرسال رابط إعادة التعيين",
        "forgot_sent": "إذا كان هناك حساب مرتبط بهذا البريد الإلكتروني، فرابط إعادة"
            " التعيين في الطريق إليك.",
        "reset_title": "تعيين كلمة مرور جديدة", "new_password": "كلمة المرور الجديدة",
        "reset_btn": "تغيير كلمة المرور",
        "account_title": "حسابي", "order_history": "سجل الطلبات",
        "th_date": "التاريخ", "th_status": "الحالة", "view": "عرض",
        "no_orders": "لا توجد طلبات بعد.",
        "saved_passengers": "المسافرون المحفوظون",
        "saved_passengers_note": "احفظ بيانات المسافرين لإعادة استخدامها في الطلبات"
            " المستقبلية. بيانات جواز السفر اختيارية وتُخزَّن مشفّرة.",
        "nationality": "الجنسية", "passport": "رقم جواز السفر",
        "passport_expiry": "تاريخ انتهاء جواز السفر",
        "add_saved_passenger": "إضافة مسافر",
        "passport_note": "اختياري. يُخزَّن مشفّراً، ويُستخدم فقط لإتمام الحجوزات الدولية.",
        "delete": "حذف", "save": "حفظ",
        "new_order_btn": "حجز جديد", "traveller_saved": "تم حفظ المسافر.",
        "pw_len": "8 أحرف على الأقل", "pw_upper": "حرف كبير واحد",
        "pw_lower": "حرف صغير واحد", "pw_digit": "رقم واحد",
        "pw_special": "رمز خاص واحد (! ? # $ ...)",
        "hero_title": "حجز طيران حقيقي في دقائق",
        "hero_sub": "<b>حجز طيران أصلي (PNR)</b> دون شراء التذكرة — يمكن التحقق منه"
                    " على موقع شركة الطيران، ويُرسل إلى بريدك الإلكتروني مع خط سير"
                    " رحلة بصيغة PDF قابل للطباعة. مثالي لـ<b>طلبات التأشيرة</b>"
                    " و<b>إثبات مواصلة السفر</b>.",
        "badge1": "PNR حقيقي قابل للتحقق", "badge2": "يُسلَّم في دقائق",
        "badge3": "خط سير رحلة PDF + تحقق عبر QR",
        "order_title": "اطلب حجزك",
        "book_need_account_text": "تتم الحجوزات من خلال حسابك — إذ يحفظ سجل حجوزاتك "
            "ويتيح لك إعادة استخدام بيانات المسافرين. "
            "إنشاء الحساب لا يستغرق سوى ثوانٍ.",
        "book_register_btn": "إنشاء حساب والحجز",
        "book_signin_btn": "لدي حساب بالفعل",
        "validity": "مدة الصلاحية",
        "plan_basic": "قياسي",
        "plan_basic_desc": "حجز واحد، صالح لمدة 24–72 ساعة (حسب شركة الطيران)",
        "plan_week": "7 أيام",
        "plan_week_desc": "يُجدَّد تلقائياً برمز PNR جديد كلما انتهت صلاحيته —"
                          " ويبقى صالحاً لمدة 7 أيام",
        "plan_2week": "14 يوماً",
        "plan_2week_desc": "تجديد تلقائي لمدة 14 يوماً — مثالي لإجراءات التأشيرة"
                           " الأطول",
        "trip_type": "نوع الرحلة",
        "oneway": "ذهاب فقط", "oneway_desc": "رحلة واحدة",
        "round": "ذهاب وعودة", "round_desc": "ذهاباً وإياباً",
        "multi": "وجهات متعددة", "multi_desc": "2–3 رحلات",
        "from": "من", "to": "إلى", "depart": "تاريخ المغادرة",
        "return": "تاريخ العودة", "flight2": "الرحلة 2",
        "flight3": "الرحلة 3 (اختياري)", "date": "التاريخ",
        "placeholder_city": "المدينة أو المطار",
        "email": "البريد الإلكتروني (يُرسل خط سير الرحلة إليه)",
        "phone": "الهاتف (بالصيغة الدولية، +34...)",
        "passenger": "المسافر", "title_lbl": "اللقب",
        "given": "الاسم الأول (كما في جواز السفر)",
        "surname": "اسم العائلة (كما في جواز السفر)",
        "dob": "تاريخ الميلاد", "gender": "الجنس",
        "male": "ذكر", "female": "أنثى",
        "add_passenger": "+ إضافة مسافر",
        "pay_method": "طريقة الدفع",
        "pay_card": "بطاقة", "pay_card_desc": "Visa وMastercard — عبر Stripe",
        "pay_crypto": "عملات مشفّرة",
        "pay_crypto_desc": "BTC وXMR وZEC وETH وUSDT — أكثر من 300 عملة",
        "submit": "احصل على حجزي",
        "fee_note": "تدفع رسوم خدمتنا فقط. لا نحمّلك أبداً سعر الرحلة، ولا يُدفع أي"
                    " مبلغ لشركة الطيران إطلاقاً.",
        "how_title": "كيف تعمل الخدمة",
        "how1": "تدفع رسوم الخدمة — ولا شيء غيرها، أبداً.",
        "how2": "نُجري حجزاً حقيقياً لدى شركة الطيران باسمك — حجزاً برمز PNR، محتفظاً"
                " به دون دفع.",
        "how3": "يصل خط سير الرحلة مع رمز PNR وملف PDF قابل للطباعة إلى بريدك الوارد،"
                " عادةً خلال دقائق. تحقق منه على موقع شركة الطيران نفسها («إدارة الحجز»).",
        "how4": "القياسي: تُلغي شركة الطيران الحجز غير المدفوع بعد 24–72 ساعة. ومع خيار"
                " 7/14 يوماً ننشئ تلقائياً حجزاً جديداً في كل مرة تنتهي فيها صلاحية"
                " الحجز ونرسل إليك رمز PNR الجديد بالبريد الإلكتروني.",
        "what_title": "ما هو — وما ليس هو",
        "what_html": "<p>تحصل على <b>حجز حقيقي</b>، وليس ملف PDF معدَّلاً: رمز PNR"
                     " موجود في نظام شركة الطيران ويمكن لأي شخص التحقق منه ما دام"
                     " صالحاً.</p><p>إنه <b>ليس تذكرة طيران</b> — لا يمكنك الصعود إلى"
                     " الطائرة به، وبعد انتهاء صلاحيته سيُظهر التحقق أنه أُلغي. تقبل"
                     " السفارات عادةً (وكثيراً ما توصي بـ) الحجوزات دون إصدار تذكرة"
                     " لطلبات التأشيرة؛ وتحافظ خيارات التجديد التلقائي على رمز PNR"
                     " ساري المفعول في بريدك الوارد طوال فترة معالجة الطلب.</p>",
        "more_faq": "هل لديك أسئلة أخرى؟ اطّلع على <a href='/faq'>الأسئلة الشائعة</a>.",
        "footer": "تقدّم حجوزات طيران دون إصدار تذكرة وحجوزات فنادق قابلة للإلغاء"
                  " لطلبات التأشيرة وإثبات مواصلة السفر. الحجز ليس تذكرة طيران ولا"
                  " إقامة مدفوعة، ولا يمكن استخدامه للصعود إلى الطائرة.",
        "st_confirmed": "تم تأكيد الحجز",
        "st_passengers": "المسافرون",
        "th_flight": "الرحلة", "th_route": "المسار",
        "th_dep": "المغادرة", "th_arr": "الوصول",
        "st_valid": "صالح حتى",
        "st_verify": "تحقق منه على موقع شركة الطيران ضمن «إدارة الحجز» باستخدام"
                     " رمز PNR واسم عائلتك. كما أُرسل خط سير الرحلة إلى",
        "st_autorenew": "التجديد التلقائي مفعّل: كلما ألغت شركة الطيران هذا الحجز،"
                        " ننشئ حجزاً جديداً ونرسل إليك رمز PNR الجديد بالبريد"
                        " الإلكتروني — حتى",
        "st_renewed": "عدد مرات التجديد:", "st_renewed_sofar": " حتى الآن.",
        "st_download": "تنزيل خط سير الرحلة بصيغة PDF",
        "st_working": "جارٍ العمل على طلبك...",
        "st_working_text": "يجري إنشاء حجزك. تتحدّث هذه الصفحة تلقائياً، وسيصلك خط"
                           " سير الرحلة أيضاً بالبريد الإلكتروني.",
        "st_expired": "انتهت صلاحية الحجز",
        "st_expired_text": "بلغ نهاية مدة صلاحيته وألغته شركة الطيران. هل تحتاج إلى"
                           " حجز جديد؟",
        "st_new_order": "قدّم طلباً جديداً",
        "st_failed": "تعذّر علينا إتمام هذا الحجز",
        "st_failed_text": "إذا كنت قد دفعت بالفعل، فسنعالج الأمر أو نردّ إليك المبلغ"
                          " كاملاً. للاستفسارات:",
        "back": "رجوع",
        "faq_title": "الأسئلة الشائعة",
        "faq_html": """
<div class="card"><h2>هل الحجز حقيقي؟</h2><p>نعم. ننشئ حجزاً فعلياً في نظام
الحجوزات لدى شركة الطيران — من النوع نفسه الذي تنشئه وكالة السفر قبل إصدار
التذكرة. وله رمز PNR حقيقي يمكنك التحقق منه على موقع شركة الطيران ضمن «إدارة
الحجز» (PNR + اسم عائلة المسافر) ما دام صالحاً.</p></div>
<div class="card"><h2>هل يمكنني السفر به؟</h2><p><b>لا.</b> الحجز ليس تذكرة — لا
يُصدر له رقم تذكرة ولا يمكن استخدامه للصعود إلى الطائرة. إنه مستند داعم لطلب
التأشيرة أو لإثبات مواصلة السفر.</p></div>
<div class="card"><h2>ما مدة صلاحيته؟</h2><p>تحتفظ شركة الطيران بالحجز غير المدفوع
لمدة 24–72 ساعة حسب الناقل. ومع خيار 7 أيام أو 14 يوماً ننشئ تلقائياً حجزاً جديداً
في كل مرة يُلغى فيها الحجز ونرسل إليك رمز PNR الجديد بالبريد الإلكتروني، لتحصل على
حجز ساري المفعول وقابل للتحقق طوال المدة.</p></div>
<div class="card"><h2>هل تقبله السفارات؟</h2><p>تطلب معظم السفارات <i>حجز طيران
أو خط سير رحلة</i> — وينصح كثير منها صراحةً <b>بعدم</b> شراء تذكرة قبل الموافقة على
التأشيرة. والحجز دون إصدار تذكرة هو المستند المعتاد لهذا الغرض. تحقق دائماً من
المتطلبات الدقيقة لسفارتك، ورتّب موعدك بحيث يكون الحجز صالحاً في يوم التحقق منه
(أو استخدم التجديد التلقائي).</p></div>
<div class="card"><h2>متى سأحصل عليه؟</h2><p>عادةً خلال دقائق من الدفع. وإذا لم
تتوفر أجرة قابلة للحجز دون دفع لمسارك وتاريخك، فسنخبرك فوراً ونردّ إليك المبلغ
كاملاً.</p></div>
<div class="card"><h2>ما سياسة الاسترداد لديكم؟</h2><p>إذا لم نتمكن من تسليم حجز
قابل للتحقق، تسترد المبلغ كاملاً — دون أي أسئلة. راجع
<a href="/terms">الشروط</a>.</p></div>""",
    },
    "pt": {
        "pw_hint": "Pelo menos 10 caracteres. Também verificamos se ela não apareceu em"
            " nenhum vazamento de dados conhecido.",
        "google_btn": "Continuar com o Google", "or": "ou",
        "link_btn": "Enviar-me um link de acesso por e-mail",
        "link_note": "Sem senha — enviamos um link de uso único, válido por 30 minutos.",
        "link_sent": "Se existir uma conta com esse e-mail, o link de acesso está a caminho.",
        "link_confirm_text": "Clique no botão para concluir o acesso neste dispositivo.",
        "link_confirm_btn": "Entrar", "password_login": "Entrar com senha",
        "register_optional": "A conta é opcional — você também pode fazer o pedido sem ela e"
            " entrar mais tarde com um link enviado por e-mail.",
        "guest_order_text": "Não é preciso ter conta: criamos uma automaticamente para o seu"
            " e-mail e você pode entrar a qualquer momento com um link de uso único enviado"
            " por e-mail. Já tem uma conta?",
        "needed_on_lbl": "Data do agendamento na embaixada ou do check-in (opcional)",
        "needed_on_note": "Informe quando a reserva precisa estar válida e nós a criaremos"
            " na noite anterior, para que esteja ativa nesse dia.",
        "calc_basic": "Criaremos sua reserva na noite anterior a esta data e a enviaremos"
            " por e-mail imediatamente — ela estará válida no dia.",
        "calc_week": "", "calc_twoweek": "Faltam mais de 60 dias — faça o pedido mais perto"
            " da data ou escolha o plano de 14 dias se precisar dela agora.",
        "sample_btn": "Ver um documento de exemplo (PDF)",
        "hotel_soon_title": "As reservas de hotel chegam em breve.",
        "hotel_soon_text": "Estamos conectando nossos parceiros de reservas de hotel. As"
            " reservas de voo já estão disponíveis.",
        "residency_lbl": "Nacionalidade do hóspede (país do passaporte, 2 letras)",
        "residency_note": "Os hotéis definem as tarifas pelo país do hóspede, p. ex. SK, DE, IN.",
        "st_scheduled": "Pagamento recebido — reserva agendada",
        "st_scheduled_text": "Para que sua reserva esteja válida na sua data, vamos criá-la"
            " e enviar o itinerário por e-mail em",
        "nav_privacy": "Privacidade",
        "meta_title": "reservas de voo e hotel para pedidos de visto",
        "meta_description": "Reservas de voo sem emissão de passagem (PNR) e reservas de"
            " hotel canceláveis para pedidos de visto e comprovante de viagem de saída,"
            " enviadas por e-mail com um PDF para impressão.",
        "test_title": "MODO DE TESTE.",
        "test_text": "As reservas criadas neste site são, por enquanto, reservas"
            " fictícias de teste: não existem no sistema de nenhuma companhia aérea ou"
            " hotel, não podem ser verificadas e NÃO devem ser usadas em um pedido de"
            " visto. Nenhum pagamento é cobrado.",
        "operated_by": "Operado por", "company_id": "N.º de registro da empresa",
        "tax_id": "N.º de identificação fiscal", "vat_id": "N.º de IVA",
        "vat_note": "Preços com IVA incluído.",
        "consent_html": "Solicito que o serviço comece imediatamente e reconheço que perco"
            " meu direito de desistência assim que a reserva for entregue. Aceito os"
            " <a href='/terms'>Termos</a> e li a"
            " <a href='/privacy'>Política de privacidade</a>.",
        "hotel_badge1": "Reserva real e cancelável",
        "hotel_badge3": "Voucher PDF + QR",
        "hotel_price_note": "por reserva, independentemente do número de noites.",
        "hotel_what_html": "<p>Você recebe uma <b>reserva de hotel real e cancelável</b>"
            " com código de reserva — mantida em uma tarifa com cancelamento gratuito e"
            " liberada automaticamente antes do prazo de cancelamento. É documentação de"
            " apoio para pedidos de visto e comprovante de hospedagem, <b>não uma estadia"
            " paga</b>.</p>",
        "st_verify_short": "Verifique-a no site da companhia aérea em “Gerenciar reserva”"
            " com o PNR e o sobrenome do passageiro.",
        "st_sent_to": "Os documentos também foram enviados para",
        "st_test_confirmed": "Reserva de TESTE — não válida, não verificável",
        "st_refunded": "Reserva cancelada",
        "st_refunded_text": "O pagamento desta reserva foi reembolsado ou contestado;"
            " por isso a reserva foi cancelada e não será renovada.",
        "hotel_released": "foi liberada antes do prazo de cancelamento gratuito.",
        "nav_order": "Pedir", "nav_faq": "FAQ", "nav_terms": "Termos",
        "nav_login": "Entrar", "nav_account": "Minha conta", "nav_logout": "Sair",
        "nav_hotel": "Hotel",
        "hotel_hero_title": "Uma reserva de hotel real para o seu visto",
        "hotel_hero_sub": "Uma <b>reserva de hotel genuína e cancelável</b> com número de"
            " confirmação — mantida em uma tarifa com cancelamento gratuito e entregue"
            " em PDF para impressão. Ideal para <b>pedidos de visto</b> e"
            " <b>comprovante de hospedagem</b>.",
        "hotel_order_title": "Peça sua reserva de hotel",
        "city_lbl": "Cidade de destino", "checkin_lbl": "Check-in",
        "checkout_lbl": "Check-out", "guest": "Hóspede", "add_guest": "+ Adicionar hóspede",
        "hotel_submit": "Obter minha reserva de hotel",
        "hotel_confirmed": "Reserva de hotel confirmada",
        "hotel_download": "Baixar reserva em PDF",
        "checkin_th": "Check-in", "checkout_th": "Check-out", "hotel_th": "Hotel",
        "login_title": "Entrar", "register_title": "Criar uma conta",
        "email_lbl": "E-mail", "password_lbl": "Senha", "min8": "mín. 8 caracteres",
        "login_btn": "Entrar", "register_btn": "Criar conta",
        "no_account": "Ainda não tem conta?", "have_account": "Já tem uma conta?",
        "forgot_link": "Esqueceu a senha?",
        "forgot_title": "Redefinir sua senha",
        "forgot_text": "Digite o e-mail da sua conta e enviaremos um link de redefinição.",
        "forgot_btn": "Enviar link de redefinição",
        "forgot_sent": "Se existir uma conta com esse e-mail, o link de redefinição está"
            " a caminho.",
        "reset_title": "Definir nova senha", "new_password": "Nova senha",
        "reset_btn": "Alterar senha",
        "account_title": "Minha conta", "order_history": "Histórico de pedidos",
        "th_date": "Data", "th_status": "Status", "view": "Ver",
        "no_orders": "Nenhum pedido ainda.",
        "saved_passengers": "Viajantes salvos",
        "saved_passengers_note": "Salve os dados dos viajantes para reutilizá-los em"
            " pedidos futuros. Os dados do passaporte são opcionais e armazenados"
            " criptografados.",
        "nationality": "Nacionalidade", "passport": "Número do passaporte",
        "passport_expiry": "Validade do passaporte",
        "add_saved_passenger": "Adicionar viajante",
        "passport_note": "Opcional. Armazenado criptografado; usado apenas para concluir"
            " reservas internacionais.",
        "delete": "Excluir", "save": "Salvar",
        "new_order_btn": "Nova reserva", "traveller_saved": "Viajante salvo.",
        "pw_len": "Pelo menos 8 caracteres", "pw_upper": "Uma letra maiúscula",
        "pw_lower": "Uma letra minúscula", "pw_digit": "Um número",
        "pw_special": "Um caractere especial (! ? # $ ...)",
        "hero_title": "Uma reserva de voo real em minutos",
        "hero_sub": "Uma <b>reserva aérea genuína (PNR)</b> sem comprar a passagem"
                    " — verificável no site da companhia aérea, enviada ao seu"
                    " e-mail com um itinerário em PDF para impressão. Ideal para"
                    " <b>pedidos de visto</b> e <b>comprovante de viagem de"
                    " saída</b>.",
        "badge1": "PNR real e verificável", "badge2": "Entrega em minutos",
        "badge3": "Itinerário em PDF + verificação por QR",
        "order_title": "Peça sua reserva",
        "book_need_account_text": "As reservas são feitas pela sua conta — ela guarda "
            "seu histórico de reservas e permite reutilizar os dados dos viajantes. "
            "Criar uma leva poucos segundos.",
        "book_register_btn": "Criar conta e reservar",
        "book_signin_btn": "Já tenho uma conta",
        "validity": "Validade",
        "plan_basic": "Padrão",
        "plan_basic_desc": "Uma reserva, válida por 24–72 h (depende da companhia aérea)",
        "plan_week": "7 dias",
        "plan_week_desc": "Renovada automaticamente com um novo PNR sempre que expira —"
                          " mantida válida por 7 dias",
        "plan_2week": "14 dias",
        "plan_2week_desc": "Renovação automática por 14 dias — ideal para processos de"
                           " visto mais longos",
        "trip_type": "Tipo de viagem",
        "oneway": "Só ida", "oneway_desc": "Um único voo",
        "round": "Ida e volta", "round_desc": "Ida e retorno",
        "multi": "Vários destinos", "multi_desc": "2–3 voos",
        "from": "Origem", "to": "Destino", "depart": "Data de partida",
        "return": "Data de volta", "flight2": "Voo 2",
        "flight3": "Voo 3 (opcional)", "date": "Data",
        "placeholder_city": "Cidade ou aeroporto",
        "email": "E-mail (o itinerário é enviado para cá)",
        "phone": "Telefone (formato internacional, +34...)",
        "passenger": "Passageiro", "title_lbl": "Tratamento",
        "given": "Nome (como no passaporte)",
        "surname": "Sobrenome (como no passaporte)",
        "dob": "Data de nascimento", "gender": "Sexo",
        "male": "Masculino", "female": "Feminino",
        "add_passenger": "+ Adicionar passageiro",
        "pay_method": "Forma de pagamento",
        "pay_card": "Cartão", "pay_card_desc": "Visa, Mastercard — via Stripe",
        "pay_crypto": "Cripto",
        "pay_crypto_desc": "BTC, XMR, ZEC, ETH, USDT — mais de 300 moedas",
        "submit": "Obter minha reserva",
        "fee_note": "Você paga apenas a nossa taxa de serviço. Nunca cobramos o preço"
                    " do voo e a companhia aérea nunca recebe pagamento.",
        "how_title": "Como funciona",
        "how1": "Você paga a taxa de serviço — nada mais, nunca.",
        "how2": "Fazemos uma reserva real com a companhia aérea em seu nome — uma"
                " reserva com código PNR, mantida sem pagamento.",
        "how3": "O itinerário com o PNR e um PDF para impressão chega à sua caixa de"
                " entrada, geralmente em minutos. Verifique-o no próprio site da"
                " companhia aérea (“Gerenciar reserva”).",
        "how4": "Padrão: a companhia aérea libera a reserva não paga após 24–72 horas."
                " Com a opção de 7/14 dias, criamos automaticamente uma nova reserva"
                " sempre que uma expira e enviamos o novo PNR por e-mail.",
        "what_title": "O que é — e o que não é",
        "what_html": "<p>Você recebe uma <b>reserva real</b>, não um PDF editado:"
                     " o PNR existe no sistema da companhia aérea e qualquer pessoa"
                     " pode verificá-lo enquanto estiver válido.</p><p><b>Não é uma"
                     " passagem aérea</b> — você não pode embarcar com ela e, depois"
                     " que expirar, a verificação a mostrará como liberada. As"
                     " embaixadas costumam aceitar (e muitas vezes recomendam)"
                     " reservas sem emissão de passagem para pedidos de visto; as"
                     " opções de renovação automática mantêm um PNR ativo na sua"
                     " caixa de entrada durante todo o processo.</p>",
        "more_faq": "Mais perguntas? Veja o <a href='/faq'>FAQ</a>.",
        "footer": "oferece reservas de voo sem emissão de passagem e reservas de hotel"
                  " canceláveis para pedidos de visto e comprovante de viagem de saída."
                  " Uma reserva não é uma passagem aérea nem uma estadia paga e não"
                  " pode ser usada para embarcar.",
        "st_confirmed": "Reserva confirmada",
        "st_passengers": "Passageiros",
        "th_flight": "Voo", "th_route": "Rota",
        "th_dep": "Partida", "th_arr": "Chegada",
        "st_valid": "Válida até",
        "st_verify": "Verifique-a no site da companhia aérea em “Gerenciar"
                     " reserva” com o PNR e o seu sobrenome. O itinerário"
                     " também foi enviado para",
        "st_autorenew": "Renovação automática ativada: sempre que a companhia aérea"
                        " liberar esta reserva, criaremos uma nova e enviaremos o"
                        " novo PNR por e-mail — até",
        "st_renewed": "Renovada", "st_renewed_sofar": " vez(es) até agora.",
        "st_download": "Baixar itinerário em PDF",
        "st_working": "Processando...",
        "st_working_text": "Sua reserva está sendo criada. Esta página é atualizada"
                           " automaticamente; o itinerário também chegará por"
                           " e-mail.",
        "st_expired": "Reserva expirada",
        "st_expired_text": "chegou ao fim da validade e foi liberada pela companhia"
                           " aérea. Precisa de uma nova?",
        "st_new_order": "Fazer um novo pedido",
        "st_failed": "Não conseguimos concluir esta reserva",
        "st_failed_text": "Se você já pagou, vamos resolver ou reembolsar o valor"
                          " integral. Dúvidas:",
        "back": "Voltar",
        "faq_title": "Perguntas frequentes",
        "faq_html": """
<div class="card"><h2>A reserva é real?</h2><p>Sim. Criamos uma reserva de verdade
no sistema de reservas da companhia aérea — do mesmo tipo que uma agência de
viagens cria antes de emitir a passagem. Ela tem um código PNR real que você pode
verificar no site da companhia aérea em “Gerenciar reserva” (PNR + sobrenome do
passageiro) enquanto estiver válida.</p></div>
<div class="card"><h2>Posso voar com ela?</h2><p><b>Não.</b> Uma reserva não é
uma passagem — nenhum número de bilhete é emitido e ela não pode ser usada para
embarcar. É documentação de apoio para um pedido de visto ou comprovante de viagem
de saída.</p></div>
<div class="card"><h2>Por quanto tempo é válida?</h2><p>A companhia aérea mantém
uma reserva não paga por 24–72 horas, dependendo da empresa. Com a opção de 7 ou
14 dias, criamos automaticamente uma nova reserva sempre que uma é liberada e
enviamos o novo PNR por e-mail, para que você tenha uma reserva ativa e
verificável durante todo o período.</p></div>
<div class="card"><h2>As embaixadas aceitam?</h2><p>A maioria das embaixadas pede
uma <i>reserva ou itinerário</i> de voo — muitas recomendam explicitamente
<b>não</b> comprar a passagem antes da aprovação do visto. Uma reserva sem emissão
de passagem é o documento padrão para essa finalidade. Sempre confira os requisitos
exatos da sua embaixada; programe o seu agendamento para que a reserva esteja
válida no dia em que for verificada (ou use a renovação automática).</p></div>
<div class="card"><h2>Em quanto tempo vou recebê-la?</h2><p>Geralmente poucos
minutos após o pagamento. Se não houver tarifa que permita reserva sem pagamento
para sua rota e data, avisaremos imediatamente e reembolsaremos o valor
integral.</p></div>
<div class="card"><h2>Qual é a política de reembolso?</h2><p>Se não conseguirmos
entregar uma reserva verificável, você recebe o reembolso integral — sem
perguntas. Veja os <a href="/terms">Termos</a>.</p></div>""",
    },
}


def pick_lang(query_lang: str, cookie_lang: str, accept_language: str) -> str:
    for candidate in (query_lang, cookie_lang):
        if candidate in STRINGS:
            return candidate
    first = (accept_language or "").strip().lower()
    for code in ("fr", "ar", "pt", "es"):
        if first.startswith(code):
            return code
    return "en"
