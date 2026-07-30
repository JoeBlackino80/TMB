"""Preklady webu (EN + ES). Itinerár, PDF a e-maily ostávajú v angličtine —
sú určené ambasádam a leteckým kontrolám.

Použitie: šablóny dostanú slovník `t` podľa jazyka požiadavky
(?lang= → cookie → Accept-Language → en).
"""

STRINGS = {
    "en": {
        "nav_order": "Order", "nav_faq": "FAQ", "nav_terms": "Terms",
        "nav_login": "Sign in", "nav_account": "My account", "nav_logout": "Sign out",
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
        "pay_crypto_desc": "BTC, ETH, USDC, USDT — via Coinbase",
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
        "footer": "sells genuine, airline-verifiable flight reservations"
                  " (no ticket issued) for visa applications and proof of"
                  " onward travel. A reservation is not a flight ticket and"
                  " cannot be used to board.",
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
        "st_failed_text": "If you already paid, reply to your confirmation"
                          " e-mail and we will make it right or refund you.",
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
        "nav_order": "Reservar", "nav_faq": "FAQ", "nav_terms": "Términos",
        "nav_login": "Entrar", "nav_account": "Mi cuenta", "nav_logout": "Salir",
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
        "pay_crypto_desc": "BTC, ETH, USDC, USDT — vía Coinbase",
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
        "footer": "vende reservas de vuelo genuinas y verificables con la"
                  " aerolínea (sin emisión de billete) para solicitudes de"
                  " visado y prueba de vuelo de salida. Una reserva no es un"
                  " billete y no permite embarcar.",
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
        "st_failed_text": "Si ya pagaste, responde al e-mail de confirmación y"
                          " lo solucionaremos o te devolveremos el dinero.",
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
}


def pick_lang(query_lang: str, cookie_lang: str, accept_language: str) -> str:
    for candidate in (query_lang, cookie_lang):
        if candidate in STRINGS:
            return candidate
    return "es" if (accept_language or "").strip().lower().startswith("es") else "en"
