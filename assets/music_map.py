# RAX3D approved music per category: 'arabic' (Hijaz oud + maqsum) or 'energetic' (default)
ARABIC = {'25-ramadan', '26-eid-al-fitr', '27-eid-al-adha', '28-national-day', '29-founding-day', '12-camping', '19-desert-atv'}
def style_for(category): return 'arabic' if category in ARABIC else 'energetic'
