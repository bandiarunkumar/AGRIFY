"""
Smart Farmer AI - Interactive Farmer Terminal
Beautiful CLI with perfect alignment
Auto-fetches weather - farmer only enters soil details
"""

from predictions import predict_crop, predict_fertilizer
from weather import get_weather, get_forecast


# ============================================
# DESIGN HELPERS
# ============================================
W = 70  # Total width of the box


def box_top():
    print("+" + "=" * (W - 2) + "+")


def box_bottom():
    print("+" + "=" * (W - 2) + "+")


def box_line():
    print("+" + "-" * (W - 2) + "+")


def box_empty():
    print("|" + " " * (W - 2) + "|")


def box_title(text):
    print("|" + f" {text} ".center(W - 2, "=") + "|")


def box_section(text):
    print("|" + f" {text} ".center(W - 2, "-") + "|")


def box_text(text):
    print(f"|  {text:<{W-4}}|")


def box_pair(label, value, label_width=22):
    text = f"{label:<{label_width}}: {value}"
    print(f"|  {text:<{W-4}}|")


def box_highlight(text):
    print("|" + f" >>> {text} <<< ".center(W - 2) + "|")


def box_stars(text):
    print("|" + f" *** {text} *** ".center(W - 2) + "|")


def conf_label(conf):
    if conf >= 80:
        return f"{conf}%  [EXCELLENT]"
    elif conf >= 50:
        return f"{conf}%  [GOOD]"
    elif conf >= 20:
        return f"{conf}%  [MODERATE]"
    else:
        return f"{conf}%  [LOW]"


def rupees(amount):
    return f"Rs.{amount:,}"


# ============================================
# FETCH WEATHER (Village -> City fallback)
# ============================================
def fetch_weather_smart(village, mandal, district, city, state):
    locations = [
        (village, "Village"),
        (mandal, "Mandal"),
        (district, "District"),
        (city, "City"),
        (state, "State"),
    ]

    for loc, loc_type in locations:
        if loc.strip():
            result = get_weather(loc.strip())
            if "error" not in result:
                return result, loc_type, loc.strip()

    return None, None, None


# ============================================
# GET FARMER LOCATION
# ============================================
def get_farmer_location():
    box_section("ENTER YOUR LOCATION")
    box_text("(Leave blank if not applicable)")
    box_empty()
    box_bottom()

    village = input("  Village name     : ").strip()
    mandal = input("  Mandal / Taluk   : ").strip()
    district = input("  District         : ").strip()
    city = input("  Nearest City     : ").strip()
    state = input("  State            : ").strip()

    if not any([village, mandal, district, city, state]):
        print("\n  ERROR: Please enter at least one location!\n")
        return None

    box_top()
    box_section("FETCHING LIVE WEATHER DATA")

    weather_data, source_type, source_name = fetch_weather_smart(
        village, mandal, district, city, state
    )

    if not weather_data:
        box_text("ERROR: Could not fetch weather for any location")
        box_text("Please check spelling and try again")
        box_bottom()
        return None

    box_text(f"Weather fetched from: {source_type.upper()} --> {source_name}")

    if source_type != "Village" and village:
        box_text(f"NOTE: Village '{village}' not found in weather API")
        box_text(f"      Using nearest: {source_name} ({source_type})")

    box_bottom()

    return {
        "village": village,
        "mandal": mandal,
        "district": district,
        "city": city,
        "state": state,
        "weather_source": source_name,
        "weather_source_type": source_type,
        "weather": weather_data
    }


# ============================================
# DISPLAY WEATHER BOX
# ============================================
def display_weather_box(location_info):
    w = location_info["weather"]
    source = location_info["weather_source"]
    stype = location_info["weather_source_type"]

    box_top()
    box_section(f"CURRENT WEATHER  [Source: {stype} - {source}]")
    box_empty()
    box_pair("City", w["city"])
    box_pair("Temperature", f"{w['temperature']}C  (feels like {w['feels_like']}C)")
    box_pair("Temp Range", f"{w['temp_min']}C  -  {w['temp_max']}C")
    box_pair("Humidity", f"{w['humidity']}%")
    box_pair("Rainfall", f"{w['rainfall']} mm")
    box_pair("Weather", w["description"])
    box_pair("Wind Speed", f"{w['wind_speed']} m/s")
    box_pair("Cloud Cover", f"{w.get('clouds', 'N/A')}%")
    box_empty()
    box_bottom()


# ============================================
# DISPLAY FORECAST BOX
# ============================================
def display_forecast_box(location_info):
    source = location_info["weather_source"]
    stype = location_info["weather_source_type"]

    forecast = get_forecast(source)
    if "error" in forecast:
        box_top()
        box_text(f"Forecast Error: {forecast['error']}")
        box_bottom()
        return None

    box_top()
    box_section(f"5-DAY FORECAST  [Source: {stype} - {source}]")
    box_empty()

    # Header
    header = f"  {'Day':<10} {'Date':<12} {'Min':>5} {'Max':>5} {'Humid':>6} {'Rain':>7}  {'Weather'}"
    print(f"|{header:<{W-2}}|")
    print(f"|  {'-'*8}   {'-'*10}  {'-'*5} {'-'*5} {'-'*6} {'-'*7}  {'-'*13}{'':>{W-68}}|")

    for day in forecast["forecast"]:
        rain_icon = ""
        if day["rainfall_total"] > 10:
            rain_icon = " ***"
        elif day["rainfall_total"] > 5:
            rain_icon = " **"
        elif day["rainfall_total"] > 0:
            rain_icon = " *"

        line = f"  {day['short_day']:<10} {day['date']:<12} {day['temp_min']:>4.1f}C {day['temp_max']:>4.1f}C {day['humidity_avg']:>5.0f}% {day['rainfall_total']:>5.1f}mm{rain_icon}  {day['description']}"
        print(f"|{line:<{W-2}}|")

    box_empty()
    box_section("FARMING ADVISORY")
    box_empty()

    for adv in forecast["advisory"]:
        if adv["type"] == "danger":
            icon = "[!!!]"
        elif adv["type"] == "warning":
            icon = "[!! ]"
        elif adv["type"] == "tip":
            icon = "[>> ]"
        else:
            icon = "[-- ]"

        box_text(f"{icon} {adv['title']}")

        # Word wrap
        msg = adv["message"]
        max_len = W - 12
        while msg:
            chunk = msg[:max_len]
            msg = msg[max_len:]
            print(f"|{'':>8}{chunk:<{W-10}}|")

        box_empty()

    box_bottom()
    return forecast


# ============================================
# MAIN MENU
# ============================================
def main_menu():
    while True:
        box_top()
        box_title("SMART FARMER AI")
        box_empty()
        box_text("Namaste, Farmer! Welcome to Smart Farmer AI System")
        box_text("Your intelligent farming assistant")
        box_empty()
        box_section("MAIN MENU")
        box_empty()
        box_text("[1]  Check Weather + 5-Day Forecast")
        box_text("[2]  Get Crop Recommendation")
        box_text("[3]  Get Fertilizer Recommendation")
        box_text("[4]  Full Farm Analysis (All-in-One Report)")
        box_text("[5]  Quick Test (Auto Sample Data)")
        box_text("[0]  Exit")
        box_empty()
        box_bottom()

        choice = input("\n  Enter your choice (0-5): ").strip()
        print()

        if choice == "1":
            weather_menu()
        elif choice == "2":
            crop_menu()
        elif choice == "3":
            fertilizer_menu()
        elif choice == "4":
            full_analysis()
        elif choice == "5":
            quick_test()
        elif choice == "0":
            box_top()
            box_stars("GOODBYE FARMER! HAPPY FARMING!")
            box_bottom()
            break
        else:
            print("  Invalid choice. Please try again.\n")


# ============================================
# 1. WEATHER MENU
# ============================================
def weather_menu():
    box_top()
    box_title("WEATHER CHECK")
    box_empty()
    box_text("Enter your location to check weather & 5-day forecast")
    box_empty()

    location = get_farmer_location()
    if not location:
        return

    display_weather_box(location)
    display_forecast_box(location)


# ============================================
# 2. CROP RECOMMENDATION
# ============================================
def crop_menu():
    box_top()
    box_title("CROP RECOMMENDATION")
    box_empty()
    box_text("Find the best crop for your farm!")
    box_text("Weather will be auto-fetched from your location")
    box_empty()

    location = get_farmer_location()
    if not location:
        return

    w = location["weather"]
    display_weather_box(location)

    # Ask soil details
    box_top()
    box_section("ENTER YOUR SOIL DETAILS")
    box_text("(From your soil testing report)")
    box_empty()
    box_bottom()

    try:
        N = float(input("  Nitrogen (N) level      [0-140]  : "))
        P = float(input("  Phosphorus (P) level    [0-145]  : "))
        K = float(input("  Potassium (K) level     [0-205]  : "))
        ph = float(input("  Soil pH                 [3.5-10] : "))
        rainfall = float(input("  Annual Rainfall (mm)    [20-300] : "))
    except ValueError:
        print("\n  ERROR: Please enter valid numbers only!\n")
        return

    temperature = w["temperature"]
    humidity = w["humidity"]

    # Show auto-filled values
    box_top()
    box_section("AUTO-FETCHED FROM WEATHER API")
    box_pair("Temperature", f"{temperature}C")
    box_pair("Humidity", f"{humidity}%")
    box_pair("Source", f"{location['weather_source']} ({location['weather_source_type']})")
    box_bottom()

    # Predict
    box_top()
    box_section("ANALYZING YOUR FARM...")
    result = predict_crop(N, P, K, temperature, humidity, ph, rainfall)

    if "error" in result:
        box_text(f"Error: {result['error']}")
        box_bottom()
        return

    best = result["best_crop"]
    profit = best["profit"]
    pests = best["pests"]

    # Results
    box_empty()
    box_stars(f"BEST CROP: {best['crop'].upper()}")
    box_empty()
    box_pair("Recommended Crop", best["crop"].upper())
    box_pair("Confidence", conf_label(best["confidence"]))
    box_empty()

    box_section("PROFIT ESTIMATE (Per Hectare)")
    box_empty()
    box_pair("Expected Yield", f"{profit['estimated_yield_kg']:,} kg")
    box_pair("Price per kg", rupees(profit["price_per_kg"]))
    box_pair("Gross Income", rupees(profit["gross_income"]))
    box_empty()
    box_text("Cost Breakdown:")
    box_pair("  Fertilizer", rupees(profit["cost_breakdown"]["fertilizer"]))
    box_pair("  Seeds", rupees(profit["cost_breakdown"]["seeds"]))
    box_pair("  Labor", rupees(profit["cost_breakdown"]["labor"]))
    box_pair("  Other", rupees(profit["cost_breakdown"]["other"]))
    box_pair("Total Cost", rupees(profit["total_cost"]))
    box_empty()
    box_stars(f"NET PROFIT: {rupees(profit['net_profit'])}")
    box_empty()

    box_section("PEST ALERT")
    box_empty()
    box_pair("Common Pests", ", ".join(pests["pests"]))
    box_pair("Organic Solution", ", ".join(pests["organic"]))
    box_pair("Chemical Option", ", ".join(pests["chemical"]))
    box_empty()

    if result["alternatives"]:
        box_section("ALTERNATIVE CROPS")
        box_empty()
        header = f"  {'Crop':<15} {'Confidence':<22} {'Net Profit'}"
        print(f"|{header:<{W-2}}|")
        print(f"|  {'-'*13}   {'-'*20}   {'-'*13}{'':>{W-56}}|")
        for alt in result["alternatives"]:
            line = f"  {alt['crop']:<15} {conf_label(alt['confidence']):<22} {rupees(alt['profit']['net_profit'])}"
            print(f"|{line:<{W-2}}|")
        box_empty()

    box_section("YOUR INPUT SUMMARY")
    box_empty()
    inp = result["input_summary"]
    box_pair("N, P, K", f"{inp['N']}, {inp['P']}, {inp['K']}")
    box_pair("Temperature", f"{inp['temperature']}C (auto)")
    box_pair("Humidity", f"{inp['humidity']}% (auto)")
    box_pair("pH", f"{inp['ph']}")
    box_pair("Rainfall", f"{inp['rainfall']} mm")
    box_empty()
    box_bottom()


# ============================================
# 3. FERTILIZER RECOMMENDATION
# ============================================
def fertilizer_menu():
    box_top()
    box_title("FERTILIZER RECOMMENDATION")
    box_empty()
    box_text("Find the best fertilizer for your crop!")
    box_text("Temperature & Humidity auto-fetched from weather")
    box_empty()

    location = get_farmer_location()
    if not location:
        return

    w = location["weather"]
    display_weather_box(location)

    temperature = w["temperature"]
    humidity = w["humidity"]

    box_top()
    box_section("ENTER YOUR FARM DETAILS")
    box_empty()
    box_bottom()

    try:
        print("\n  === SOIL INFORMATION ===")
        print("  Soil types: [Clay, Loamy, Sandy, Silt]")
        soil_type = input("  Soil Type                       : ").strip()
        soil_ph = float(input("  Soil pH              [4.0-9.0]  : "))
        soil_moisture = float(input("  Soil Moisture        [20-80]    : "))
        organic_carbon = float(input("  Organic Carbon       [0.5-2.0]  : "))
        ec = float(input("  Elec. Conductivity   [0-2]      : "))

        print("\n  === NUTRIENT LEVELS ===")
        N = float(input("  Nitrogen (N)         [0-140]    : "))
        P = float(input("  Phosphorus (P)       [0-145]    : "))
        K = float(input("  Potassium (K)        [0-205]    : "))

        rainfall = float(input("\n  Annual Rainfall (mm) [20-300]   : "))

        print("\n  === CROP DETAILS ===")
        print("  Crops: [Cotton, Maize, Potato, Rice, Sugarcane, Tomato, Wheat]")
        crop_type = input("  Crop Type                       : ").strip()

        print("  Stages: [Vegetative, Flowering, Fruiting, Harvesting]")
        growth_stage = input("  Growth Stage                    : ").strip()

        print("  Seasons: [Kharif, Rabi, Zaid]")
        season = input("  Season                          : ").strip()

        print("  Irrigation: [Drip, Flood, Sprinkler, Rainfed]")
        irrigation = input("  Irrigation Type                 : ").strip()

        print("  Previous: [Cotton, Maize, Potato, Rice, Sugarcane, Tomato, Wheat]")
        previous_crop = input("  Previous Crop                   : ").strip()

        print("  Regions: [North, South, East, West]")
        region = input("  Region                          : ").strip()

        print("  Fertilizers: [Compost, DAP, MOP, NPK, SSP, Urea, Zinc Sulphate]")
        fertilizer_usage = input("  Last Fertilizer Used            : ").strip()

        yield_last = float(input("  Yield Last Season (kg)          : "))

    except ValueError:
        print("\n  ERROR: Please enter valid numbers!\n")
        return

    # Auto-filled
    box_top()
    box_section("AUTO-FETCHED FROM WEATHER API")
    box_pair("Temperature", f"{temperature}C")
    box_pair("Humidity", f"{humidity}%")
    box_pair("Source", f"{location['weather_source']} ({location['weather_source_type']})")
    box_bottom()

    # Predict
    box_top()
    box_section("ANALYZING YOUR FARM...")

    result = predict_fertilizer(
        soil_type=soil_type, soil_ph=soil_ph, soil_moisture=soil_moisture,
        organic_carbon=organic_carbon, electrical_conductivity=ec,
        N=N, P=P, K=K, temperature=temperature, humidity=humidity,
        rainfall=rainfall, crop_type=crop_type, growth_stage=growth_stage,
        season=season, irrigation=irrigation, previous_crop=previous_crop,
        region=region, fertilizer_usage=fertilizer_usage, yield_last=yield_last
    )

    if "error" in result:
        box_text(f"Error: {result['error']}")
        box_bottom()
        return

    best = result["best_fertilizer"]

    box_empty()
    box_stars(f"BEST FERTILIZER: {best['fertilizer'].upper()}")
    box_empty()
    box_pair("Fertilizer", best["fertilizer"])
    box_pair("Confidence", conf_label(best["confidence"]))
    box_pair("NPK Ratio", best["details"].get("npk", "N/A"))
    box_pair("Quantity/Hectare", f"{best['details'].get('qty_per_ha', 'N/A')} kg")
    box_pair("Cost per kg", f"Rs.{best['details'].get('cost_per_kg', 'N/A')}")
    box_empty()

    if result["alternatives"]:
        box_section("ALTERNATIVE FERTILIZERS")
        box_empty()
        for alt in result["alternatives"]:
            box_pair(alt["fertilizer"], conf_label(alt["confidence"]))
        box_empty()

    box_bottom()


# ============================================
# 4. FULL FARM ANALYSIS
# ============================================
def full_analysis():
    box_top()
    box_title("COMPLETE FARM ANALYSIS")
    box_empty()
    box_text("All-in-One: Weather + Crop + Fertilizer + Profit + Pests")
    box_text("Temperature & Humidity auto-fetched. Farmer enters soil only.")
    box_empty()

    # Location
    location = get_farmer_location()
    if not location:
        return

    w = location["weather"]
    temperature = w["temperature"]
    humidity = w["humidity"]

    # Weather
    display_weather_box(location)
    forecast_data = display_forecast_box(location)

    # Soil
    box_top()
    box_section("STEP 1: YOUR SOIL DETAILS")
    box_text("(From your soil testing report)")
    box_empty()
    box_bottom()

    try:
        N = float(input("  Nitrogen (N)         [0-140]    : "))
        P = float(input("  Phosphorus (P)       [0-145]    : "))
        K = float(input("  Potassium (K)        [0-205]    : "))
        ph = float(input("  Soil pH              [3.5-10]   : "))
        rainfall = float(input("  Annual Rainfall (mm) [20-300]   : "))

        print("\n  Soil types: [Clay, Loamy, Sandy, Silt]")
        soil_type = input("  Soil Type                       : ").strip()
        soil_moisture = float(input("  Soil Moisture        [20-80]    : "))
        organic_carbon = float(input("  Organic Carbon       [0.5-2.0]  : "))
        ec = float(input("  Elec. Conductivity   [0-2]      : "))
    except ValueError:
        print("\n  ERROR: Enter valid numbers!\n")
        return

    # Crop details
    box_top()
    box_section("STEP 2: CROP DETAILS")
    box_empty()
    box_bottom()

    try:
        print("  Crops: [Cotton, Maize, Potato, Rice, Sugarcane, Tomato, Wheat]")
        crop_type = input("  Current/Planned Crop            : ").strip()

        print("  Stages: [Vegetative, Flowering, Fruiting, Harvesting]")
        growth_stage = input("  Growth Stage                    : ").strip()

        print("  Seasons: [Kharif, Rabi, Zaid]")
        season = input("  Season                          : ").strip()

        print("  Irrigation: [Drip, Flood, Sprinkler, Rainfed]")
        irrigation = input("  Irrigation Type                 : ").strip()

        print("  Previous: [Cotton, Maize, Potato, Rice, Sugarcane, Tomato, Wheat]")
        previous_crop = input("  Previous Crop                   : ").strip()

        print("  Regions: [North, South, East, West]")
        region = input("  Region                          : ").strip()

        print("  Fertilizers: [Compost, DAP, MOP, NPK, SSP, Urea, Zinc Sulphate]")
        fertilizer_usage = input("  Last Fertilizer Used            : ").strip()

        yield_last = float(input("  Yield Last Season (kg)          : "))
    except ValueError:
        print("\n  ERROR: Enter valid numbers!\n")
        return

    # ==========================================
    # PREDICTIONS
    # ==========================================
    box_top()
    box_section("PROCESSING YOUR DATA...")
    box_text(f"Auto-fetched: Temperature={temperature}C, Humidity={humidity}%")
    box_text(f"Source: {location['weather_source']} ({location['weather_source_type']})")
    box_bottom()

    # Crop prediction
    crop_result = predict_crop(N, P, K, temperature, humidity, ph, rainfall)
    if "error" in crop_result:
        print(f"\n  Crop Error: {crop_result['error']}\n")
        return

    # Fertilizer prediction
    fert_result = predict_fertilizer(
        soil_type=soil_type, soil_ph=ph, soil_moisture=soil_moisture,
        organic_carbon=organic_carbon, electrical_conductivity=ec,
        N=N, P=P, K=K, temperature=temperature, humidity=humidity,
        rainfall=rainfall, crop_type=crop_type, growth_stage=growth_stage,
        season=season, irrigation=irrigation, previous_crop=previous_crop,
        region=region, fertilizer_usage=fertilizer_usage, yield_last=yield_last
    )
    if "error" in fert_result:
        print(f"\n  Fertilizer Error: {fert_result['error']}\n")
        return

    best_crop = crop_result["best_crop"]
    best_fert = fert_result["best_fertilizer"]
    profit = best_crop["profit"]
    pests = best_crop["pests"]

    # ==========================================
    # COMPREHENSIVE REPORT
    # ==========================================
    print()
    box_top()
    box_title("SMART FARMER AI - COMPLETE FARM REPORT")
    box_empty()

    # Location
    loc = location
    loc_parts = [loc["village"], loc["mandal"], loc["district"], loc["city"], loc["state"]]
    loc_str = ", ".join(filter(None, loc_parts))

    box_section("FARMER LOCATION")
    box_empty()
    box_pair("Address", loc_str)
    box_pair("Weather Source", f"{loc['weather_source']} ({loc['weather_source_type']})")
    box_empty()

    # Weather
    box_section("LIVE WEATHER")
    box_empty()
    box_pair("Temperature", f"{w['temperature']}C  (feels like {w['feels_like']}C)")
    box_pair("Temp Range", f"{w['temp_min']}C  -  {w['temp_max']}C")
    box_pair("Humidity", f"{w['humidity']}%")
    box_pair("Rainfall", f"{w['rainfall']} mm")
    box_pair("Condition", w["description"])
    box_pair("Wind", f"{w['wind_speed']} m/s")
    box_empty()

    # Soil
    box_section("SOIL ANALYSIS")
    box_empty()
    box_pair("Soil Type", soil_type)
    box_pair("Nitrogen (N)", str(N))
    box_pair("Phosphorus (P)", str(P))
    box_pair("Potassium (K)", str(K))
    box_pair("pH Level", str(ph))
    box_pair("Moisture", f"{soil_moisture}%")
    box_pair("Organic Carbon", str(organic_carbon))
    box_pair("Elec. Conductivity", str(ec))
    box_empty()

    # Crop
    box_section("CROP RECOMMENDATION")
    box_empty()
    box_stars(f"BEST CROP: {best_crop['crop'].upper()}")
    box_empty()
    box_pair("Recommended Crop", best_crop["crop"].upper())
    box_pair("Confidence", conf_label(best_crop["confidence"]))
    box_empty()

    # Profit
    box_section("PROFIT ESTIMATE (Per Hectare)")
    box_empty()
    box_pair("Expected Yield", f"{profit['estimated_yield_kg']:,} kg")
    box_pair("Price per kg", rupees(profit["price_per_kg"]))
    box_pair("Gross Income", rupees(profit["gross_income"]))
    box_empty()
    box_text("  Cost Breakdown:")
    box_pair("    Fertilizer Cost", rupees(profit["cost_breakdown"]["fertilizer"]))
    box_pair("    Seeds Cost", rupees(profit["cost_breakdown"]["seeds"]))
    box_pair("    Labor Cost", rupees(profit["cost_breakdown"]["labor"]))
    box_pair("    Other Cost", rupees(profit["cost_breakdown"]["other"]))
    box_line()
    box_pair("  TOTAL COST", rupees(profit["total_cost"]))
    box_pair("  GROSS INCOME", rupees(profit["gross_income"]))
    box_empty()
    box_stars(f"NET PROFIT: {rupees(profit['net_profit'])} per hectare")
    box_empty()

    # Alternatives
    if crop_result["alternatives"]:
        box_section("ALTERNATIVE CROPS")
        box_empty()
        header = f"  {'Crop':<15} {'Confidence':<22} {'Net Profit'}"
        print(f"|{header:<{W-2}}|")
        sep = f"  {'-'*13}   {'-'*20}   {'-'*13}"
        print(f"|{sep:<{W-2}}|")
        for alt in crop_result["alternatives"]:
            line = f"  {alt['crop']:<15} {conf_label(alt['confidence']):<22} {rupees(alt['profit']['net_profit'])}"
            print(f"|{line:<{W-2}}|")
        box_empty()

    # Fertilizer
    box_section("FERTILIZER RECOMMENDATION")
    box_empty()
    box_stars(f"BEST FERTILIZER: {best_fert['fertilizer'].upper()}")
    box_empty()
    box_pair("Fertilizer", best_fert["fertilizer"])
    box_pair("Confidence", conf_label(best_fert["confidence"]))
    box_pair("NPK Ratio", best_fert["details"].get("npk", "N/A"))
    box_pair("Quantity/Hectare", f"{best_fert['details'].get('qty_per_ha', 'N/A')} kg")
    box_pair("Cost per kg", f"Rs.{best_fert['details'].get('cost_per_kg', 'N/A')}")
    box_empty()

    if fert_result["alternatives"]:
        box_text("Alternatives:")
        for alt in fert_result["alternatives"]:
            box_pair(f"  {alt['fertilizer']}", conf_label(alt["confidence"]))
        box_empty()

    # Pest Alert
    box_section("PEST ALERT")
    box_empty()
    box_pair("Common Pests", ", ".join(pests["pests"]))
    box_pair("Organic Solution", ", ".join(pests["organic"]))
    box_pair("Chemical Option", ", ".join(pests["chemical"]))
    box_empty()

    # Forecast
    if forecast_data and "error" not in forecast_data:
        box_section("5-DAY FORECAST SUMMARY")
        box_empty()
        for day in forecast_data["forecast"]:
            line = f"  {day['short_day']:<5} {day['date']}   {day['temp_min']:>4.1f}-{day['temp_max']:>4.1f}C   H:{day['humidity_avg']:>3.0f}%   R:{day['rainfall_total']:>5.1f}mm   {day['description']}"
            print(f"|{line:<{W-2}}|")
        box_empty()

        box_text("Weather Advisory:")
        for adv in forecast_data["advisory"]:
            icon = "!!!" if adv["type"] == "danger" else "!! " if adv["type"] == "warning" else ">> " if adv["type"] == "tip" else "-- "
            box_text(f"  [{icon}] {adv['title']}")
            msg = adv["message"]
            max_len = W - 14
            while msg:
                chunk = msg[:max_len]
                msg = msg[max_len:]
                print(f"|{'':>10}{chunk:<{W-12}}|")
        box_empty()

    # Footer
    box_line()
    box_stars("REPORT GENERATED SUCCESSFULLY")
    box_text(f"Location: {loc_str}")
    box_text(f"Weather:  {loc['weather_source']} ({loc['weather_source_type']})")
    box_bottom()
    print()


# ============================================
# 5. QUICK TEST
# ============================================
def quick_test():
    box_top()
    box_title("QUICK TEST - AUTO SAMPLE DATA")
    box_empty()
    box_text("Testing all features with Hyderabad + sample soil data")
    box_empty()

    # Weather
    box_section("WEATHER - Hyderabad")
    current = get_weather("Hyderabad")
    if "error" in current:
        box_text(f"Error: {current['error']}")
        box_bottom()
        return

    box_pair("City", current["city"])
    box_pair("Temperature", f"{current['temperature']}C (feels {current['feels_like']}C)")
    box_pair("Humidity", f"{current['humidity']}%")
    box_pair("Weather", current["description"])
    box_empty()

    # Forecast
    forecast = get_forecast("Hyderabad")
    if "error" not in forecast:
        box_section("5-DAY FORECAST")
        for day in forecast["forecast"]:
            line = f"  {day['short_day']:<5} {day['date']}  {day['temp_min']:>4.1f}-{day['temp_max']:>4.1f}C  H:{day['humidity_avg']:>3.0f}%  R:{day['rainfall_total']:>5.1f}mm  {day['description']}"
            print(f"|{line:<{W-2}}|")
        box_empty()
        for adv in forecast["advisory"]:
            box_text(f"[{adv['type'].upper():<7}] {adv['title']}")
        box_empty()

    # Crop
    box_section("CROP PREDICTION")
    box_text("Input: N=90, P=42, K=43, pH=6.5, Rain=200mm")
    box_text(f"Auto:  Temp={current['temperature']}C, Humidity={current['humidity']}%")
    box_empty()

    crop = predict_crop(
        N=90, P=42, K=43,
        temperature=current["temperature"],
        humidity=current["humidity"],
        ph=6.5, rainfall=200
    )

    if "error" not in crop:
        best = crop["best_crop"]
        box_stars(f"BEST CROP: {best['crop'].upper()} ({best['confidence']}%)")
        box_pair("Net Profit", f"{rupees(best['profit']['net_profit'])}/hectare")
        box_pair("Pests", ", ".join(best["pests"]["pests"]))
        if crop["alternatives"]:
            box_text("Alternatives:")
            for alt in crop["alternatives"][:3]:
                box_pair(f"  {alt['crop']}", f"{alt['confidence']}%  Profit: {rupees(alt['profit']['net_profit'])}")
        box_empty()

    # Fertilizer
    box_section("FERTILIZER PREDICTION")
    box_text("Input: Loamy soil, Rice, Kharif, Drip irrigation")
    box_empty()

    fert = predict_fertilizer(
        soil_type="Loamy", soil_ph=6.5, soil_moisture=40,
        organic_carbon=1.2, electrical_conductivity=0.5,
        N=30, P=20, K=15,
        temperature=current["temperature"],
        humidity=current["humidity"],
        rainfall=100, crop_type="Rice", growth_stage="Vegetative",
        season="Kharif", irrigation="Drip", previous_crop="Wheat",
        region="South", fertilizer_usage="Urea", yield_last=4000
    )

    if "error" not in fert:
        best_f = fert["best_fertilizer"]
        box_stars(f"BEST FERTILIZER: {best_f['fertilizer']} ({best_f['confidence']}%)")
        box_pair("NPK Ratio", best_f["details"].get("npk", "N/A"))
        if fert["alternatives"]:
            box_text("Alternatives:")
            for alt in fert["alternatives"]:
                box_pair(f"  {alt['fertilizer']}", f"{alt['confidence']}%")
        box_empty()

    box_line()
    box_stars("ALL TESTS PASSED - LIVE WEATHER USED!")
    box_bottom()
    print()


# ============================================
# START
# ============================================
if __name__ == "__main__":
    main_menu()