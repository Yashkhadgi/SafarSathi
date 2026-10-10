"""API Router exposing safe P0 and P1 travel tools to the React UI."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.app.api.deps import get_current_user
from backend.app.db.models.user import User

# P0 Tool imports
from tools.itinerary_tool import build_itinerary, edit_itinerary, validate_itinerary, itinerary_markdown
from memory.trips import get_trip, latest_trip, undo_trip, trip_versions
from tools.budget_tool import estimate_budget, compare_budget_tiers
from tools.currency_tool import convert_currency
from tools.transport_tools import how_to_reach, get_local_transport
from tools.scam_tool import get_scam_alerts

# P1 Tool imports
from tools.weather_tool import get_forecast
from tools.realtime_tool import get_live_weather, get_opening_hours, near_me, air_quality_advice
from tools.safety_tool import get_area_safety, get_medical_help, get_lost_docs_help
from tools.entry_fees_tool import get_entry_fees
from tools.budget_ext_tool import check_fair_price, atm_info
from tools.transport_ext_tool import get_train_bus_info, get_stay_areas
from tools.knowledge_tool import get_food_guide, get_temple_guide, get_etiquette
from tools.planning_tool import theme_trip_weights, traveler_type_notes, plan_b_alternatives
from tools.recommender_tool import recommend_destinations, best_time_to_visit
from tools.optimizer_tool import optimize_route
from tools.checklist_tool import smart_packing_list, pre_trip_checklist
from tools.export_tool import export_itinerary_text, export_itinerary_ics, export_itinerary_pdf
from tools.phrasebook import phrase_for, emergency_phrase, get_all_phrases, get_all_emergency_phrases

tools_router = APIRouter(prefix="/tools", tags=["Tools"])


# --- P0 Tool Endpoints ---

class ItineraryBuildRequest(BaseModel):
    destination: str
    days: int
    interests: Optional[List[str]] = None
    pace: Optional[str] = "normal"
    month: Optional[str] = None
    theme: Optional[str] = None
    traveler_type: Optional[str] = None

class ItineraryEditRequest(BaseModel):
    trip_id: Optional[str] = None
    instructions: Optional[str] = None
    instruction: Optional[str] = None

    def get_instruction_text(self) -> str:
        return self.instructions or self.instruction or ""

class BudgetEstimateRequest(BaseModel):
    destination: str
    days: int
    traveler_type: Optional[str] = "solo"
    tier: Optional[str] = "mid"
    origin: Optional[str] = None

class HowToReachRequest(BaseModel):
    destination: str
    origin: Optional[str] = None


@tools_router.post("/itinerary/build")
def api_build_itinerary(req: ItineraryBuildRequest, user: User = Depends(get_current_user)):
    session_id = f"user_{user.id}"
    return build_itinerary(
        destination=req.destination,
        days=req.days,
        pace=req.pace or "normal",
        session_id=session_id,
        travelers=1,
    )


@tools_router.post("/itinerary/edit")
def api_edit_itinerary(req: ItineraryEditRequest, user: User = Depends(get_current_user)):
    session_id = f"user_{user.id}"
    return edit_itinerary(trip_id=req.trip_id or "", instruction=req.get_instruction_text(), session_id=session_id)


@tools_router.post("/itinerary/undo")
def api_undo_itinerary(trip_id: str = Query("", description="Trip ID"), user: User = Depends(get_current_user)):
    session_id = f"user_{user.id}"
    return undo_trip(trip_id=trip_id, session_id=session_id)


@tools_router.get("/itinerary/active")
def api_get_active_itinerary(user: User = Depends(get_current_user)):
    session_id = f"user_{user.id}"
    active = latest_trip(session_id)
    versions = trip_versions(active.get("trip_id", ""), session_id) if isinstance(active, dict) and "trip_id" in active else []
    return {"itinerary": active, "versions": versions}


@tools_router.post("/budget/estimate")
def api_estimate_budget(req: BudgetEstimateRequest):
    trip_dict = {"destination": req.destination, "days": [{"day": i + 1} for i in range(max(1, req.days))]}
    return estimate_budget(
        trip=trip_dict,
        travelers=1,
        tier=req.tier or "mid",
    )


@tools_router.get("/budget/tiers")
def api_budget_tiers(
    destination: str = Query(..., description="Destination city"),
    days: int = Query(3, description="Duration in days"),
    travelers: int = Query(1, description="Number of travelers")
):
    trip_dict = {"destination": destination, "days": [{"day": i + 1} for i in range(max(1, days))]}
    return compare_budget_tiers(trip=trip_dict, travelers=travelers)


@tools_router.get("/transport/reach")
def api_how_to_reach(
    destination: str = Query(..., description="Destination city"),
    origin: str = Query("", description="Origin city")
):
    return how_to_reach(destination=destination, origin=origin)


@tools_router.get("/transport/local")
def api_local_transport(destination: str = Query(..., description="City")):
    return get_local_transport(city=destination)


@tools_router.get("/scams")
def api_scam_alerts(
    city: str = Query(..., description="City name"),
    location_type: str = Query("", description="Location type")
):
    return get_scam_alerts(city=city, location_type=location_type)


# --- P1 Tool Endpoints ---

@tools_router.get("/weather")
def api_weather(
    destination: str = Query(..., description="Destination name"),
    days: int = Query(3, description="Days to forecast")
):
    return get_live_weather(place=destination, days=days)


@tools_router.get("/hours")
def api_opening_hours(
    place: str = Query(..., description="Attraction or monument name"),
    city: str = Query("", description="City name"),
    visit_date: str = Query("", description="Date YYYY-MM-DD")
):
    from datetime import datetime, timezone
    target_date = visit_date or datetime.now(timezone.utc).date().isoformat()
    return get_opening_hours(place=place, city=city, visit_date=target_date)


@tools_router.get("/near-me")
def api_near_me(
    latitude: Optional[float] = Query(None, description="User latitude"),
    longitude: Optional[float] = Query(None, description="User longitude"),
    city: str = Query("", description="City name"),
    category: str = Query("attractions", description="Category: attractions, restaurants, atm, petrol, pharmacy"),
    open_now: bool = Query(False, description="Open now filter"),
    veg: bool = Query(False, description="Pure veg filter"),
    min_rating: float = Query(0.0, description="Minimum rating"),
    consent: bool = Query(True, description="Location consent")
):
    return near_me(
        latitude=latitude,
        longitude=longitude,
        city=city,
        kind=category,
        open_now=open_now,
        veg=veg,
        min_rating=min_rating,
        consent=consent,
    )


@tools_router.get("/safety/area")
def api_area_safety(
    city: str = Query(..., description="City or region name"),
    context: str = Query("", description="Context e.g. night, solo female")
):
    return get_area_safety(city=city, context=context)


@tools_router.get("/safety/medical")
def api_medical_help(
    symptom: str = Query(..., description="Symptom or emergency"),
    city: str = Query("", description="Current city")
):
    return get_medical_help(symptom=symptom, city=city)


@tools_router.get("/safety/lost-docs")
def api_lost_docs(
    what_lost: str = Query(..., description="Document lost: passport, phone, wallet, aadhar"),
    nationality: str = Query("Indian", description="Nationality")
):
    return get_lost_docs_help(what_lost=what_lost, nationality=nationality)


@tools_router.get("/budget/entry-fees")
def api_entry_fees(place: str = Query(..., description="Monument or site name")):
    return get_entry_fees(place=place)


@tools_router.get("/budget/fair-prices")
def api_fair_prices(
    city: str = Query(..., description="City name"),
    category: str = Query("", description="Category: auto, taxi, bus, metro, meal")
):
    return check_fair_price(city=city, transport_type=category)


@tools_router.get("/budget/atm")
def api_atm_info(city: str = Query("", description="City name")):
    return atm_info(city=city)


@tools_router.get("/budget/currency")
def api_currency(
    amount: float = Query(..., description="Amount"),
    from_curr: str = Query("USD", description="Source currency"),
    to_curr: str = Query("INR", description="Target currency")
):
    return convert_currency(amount=amount, from_currency=from_curr, to_currency=to_curr)


@tools_router.get("/transport/train-bus")
def api_train_bus(
    origin: str = Query(..., description="Origin city"),
    destination: str = Query(..., description="Destination city")
):
    return get_train_bus_info(origin=origin, destination=destination)


@tools_router.get("/stay/areas")
def api_stay_areas(
    city: str = Query(..., description="City name"),
    traveler_type: str = Query("", description="Traveler profile")
):
    return get_stay_areas(city=city, traveler_type=traveler_type)


@tools_router.get("/knowledge/food")
def api_food_guide(
    city: str = Query(..., description="City name"),
    diet_filter: str = Query("", description="veg, vegan, jain, halal")
):
    return get_food_guide(city=city, diet_filter=diet_filter)


@tools_router.get("/knowledge/temple")
def api_temple_guide(site_or_city: str = Query(..., description="Temple or site name")):
    return get_temple_guide(site_or_city=site_or_city)


@tools_router.get("/knowledge/etiquette")
def api_etiquette(state_or_religion: str = Query("", description="State or religion")):
    return get_etiquette(state_or_religion=state_or_religion)


@tools_router.get("/planning/theme-weights")
def api_theme_weights(theme: str = Query(..., description="Theme name")):
    return theme_trip_weights(theme=theme)


@tools_router.get("/planning/traveler-notes")
def api_traveler_notes(traveler_type: str = Query(..., description="Traveler type")):
    return traveler_type_notes(traveler_type=traveler_type)


@tools_router.post("/planning/plan-b")
def api_plan_b(
    itinerary: Dict[str, Any],
    weather_condition: Optional[str] = "rain"
):
    return plan_b_alternatives(itinerary=itinerary, weather_data={"condition": weather_condition})


@tools_router.get("/recommender/destinations")
def api_recommender(
    budget_inr: float = Query(15000, description="Budget in INR"),
    days: int = Query(4, description="Days"),
    month: str = Query("October", description="Month"),
    mood: str = Query("heritage", description="Mood / Theme"),
    origin_city: str = Query("Delhi", description="Origin city")
):
    return recommend_destinations(
        budget_inr=budget_inr,
        days=days,
        month=month,
        mood=mood,
        origin_city=origin_city,
    )


@tools_router.get("/recommender/best-time")
def api_best_time(place: str = Query(..., description="Destination name")):
    return best_time_to_visit(place=place)


@tools_router.post("/optimizer/route")
def api_optimize_route(
    cities: List[str],
    origin: str = "Delhi",
    total_days: int = 7
):
    return optimize_route(cities=cities, origin=origin, total_days=total_days)


@tools_router.get("/checklist/packing")
def api_packing_list(
    destination: str = Query(..., description="Destination"),
    days: int = Query(4, description="Duration"),
    season: str = Query("", description="Season"),
    traveler_type: str = Query("", description="Profile"),
    activities: str = Query("", description="Comma-separated activities")
):
    act_list = [a.strip() for a in activities.split(",") if a.strip()]
    return smart_packing_list(
        destination=destination,
        days=days,
        activities=act_list,
        season=season,
        traveler_type=traveler_type,
    )


@tools_router.get("/checklist/pre-trip")
def api_pre_trip(
    destination: str = Query(..., description="Destination"),
    trip_start_date: str = Query("", description="Start date YYYY-MM-DD"),
    is_international: bool = Query(False, description="International traveler")
):
    return pre_trip_checklist(
        trip_start_date=trip_start_date,
        destination=destination,
        is_international=is_international,
    )


@tools_router.get("/phrasebook")
def api_phrasebook(situation: str = Query("", description="Situation"), language: str = Query("", description="Language code")):
    if situation and language:
        return phrase_for(situation=situation, language=language)
    return get_all_phrases()


@tools_router.get("/phrasebook/emergency")
def api_emergency_phrases(language: str = Query("", description="Language code")):
    if language:
        return emergency_phrase(language=language)
    return get_all_emergency_phrases()


@tools_router.post("/export/text")
def api_export_text(
    trip_data: Dict[str, Any],
    user: User = Depends(get_current_user)
):
    session_id = f"user_{user.id}"
    return export_itinerary_text(trip_id="active", session_id=session_id)


@tools_router.post("/export/ics")
def api_export_ics(
    trip_data: Dict[str, Any],
    user: User = Depends(get_current_user)
):
    session_id = f"user_{user.id}"
    return export_itinerary_ics(trip_id="active", session_id=session_id)
