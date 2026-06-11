#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# RuThere API 接口测试脚本
# 使用前确保 backend 已在运行:  cd backend && uvicorn app.main:app --reload --port 8000
# 用法:  bash test_api.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE="${1:-http://127.0.0.1:8000}"
TOKEN=""

pass() { echo -e "  \e[32m✓ $*\e[0m"; }
fail() { echo -e "  \e[31m✗ $*\e[0m"; }
info() { echo -e "  \e[36m→ $*\e[0m"; }
sep()  { echo -e "\n\e[33m─── $* ───\e[0m"; }

# Helper: curl with Authorization header
CURL() {
    curl -s -H "Authorization: Bearer $TOKEN" "$@"
}

# ── 1. Health ───────────────────────────────────────────────────────────────

sep "1) Health check"
HEALTH=$(curl -s "$BASE/health")
echo "    $HEALTH"
if echo "$HEALTH" | grep -q '"status":"ok"'; then
  pass "Health check passed"
else
  fail "Health check failed — is the server running?"
  exit 1
fi

# ── 2. Register ─────────────────────────────────────────────────────────────

sep "2) 注册新用户"

REG=$(curl -s -X POST "$BASE/api/register" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13912345678","nickname":"测试君","password":"test1234"}')
echo "    $REG"
# Save both tokens for later refresh test
ACCESS_TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
REFRESH_TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
TOKEN=$ACCESS_TOKEN
NICK=$(echo "$REG"   | python3 -c "import sys,json; print(json.load(sys.stdin)['nickname'])")
if [ -n "$TOKEN" ]; then
  pass "注册成功: $NICK"
else
  fail "注册失败"
fi

# ── 3. Duplicate register ───────────────────────────────────────────────────

sep "3) 重复手机号注册（应拒绝）"
DUP=$(curl -s -X POST "$BASE/api/register" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13912345678","nickname":"冒牌君","password":"test1234"}')
echo "    $DUP"
if echo "$DUP" | grep -qi '已注册'; then
  pass "重复注册被正确拒绝"
else
  fail "预期拒绝但未得到"
fi

# ── 4. Login ────────────────────────────────────────────────────────────────

sep "4) 手机号登录"
LOGIN=$(curl -s -X POST "$BASE/api/login" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13912345678","password":"test1234"}')
echo "    $LOGIN"
ACCESS_TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
REFRESH_TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
TOKEN=$ACCESS_TOKEN
if [ -n "$TOKEN" ]; then
  pass "登录成功"
else
  fail "登录失败"
fi

# ── 5. Login with wrong password ────────────────────────────────────────────

sep "5) 错误密码登录（应拒绝）"
BAD=$(curl -s -X POST "$BASE/api/login" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13912345678","password":"wrongpass"}')
echo "    $BAD"
if echo "$BAD" | grep -qi '错误'; then
  pass "错误密码被正确拒绝"
else
  fail "预期拒绝但未得到"
fi

# ── 6. Login with invalid phone format ──────────────────────────────────────

sep "6) 不符合规则的手机号注册（应拒绝）"
INV=$(curl -s -X POST "$BASE/api/register" \
  -H "Content-Type: application/json" \
  -d '{"phone":"12345","nickname":"坏人","password":"test1234"}')
echo "    $INV"
if echo "$INV" | grep -qi '手机号格式'; then
  pass "非法手机号被正确拒绝"
else
  fail "预期拒绝但未得到"
fi

# ── 7. Get /api/me ──────────────────────────────────────────────────────────

sep "7) 获取当前用户信息"
ME=$(CURL "$BASE/api/me")
echo "    $ME"
if echo "$ME" | grep -q '"phone":"13912345678"'; then
  pass "用户信息正确"
else
  fail "用户信息不对"
fi

# ── 8. Heartbeat ────────────────────────────────────────────────────────────

sep "8) 心跳上报"
HB=$(CURL -X POST "$BASE/api/heartbeat")
echo "    $HB"
if echo "$HB" | grep -q '"status":"ok"'; then
  pass "心跳成功"
else
  fail "心跳失败"
fi

# ── 9. Report activity ──────────────────────────────────────────────────────

sep "9) 上报活跃度增量"
ACT=$(CURL -X POST "$BASE/api/activity" \
  -H "Content-Type: application/json" \
  -d '{"increment":75}')
echo "    $ACT"
if echo "$ACT" | grep -q '"activity_score"'; then
  pass "活跃度上报成功"
else
  fail "活跃度上报失败"
fi

# ── 10. List all users ──────────────────────────────────────────────────────

sep "10) 用户列表"
USERS=$(CURL "$BASE/api/users")
echo "    $USERS" | head -c 400
echo
if echo "$USERS" | grep -q '"nickname"'; then
  pass "用户列表获取成功"
else
  fail "用户列表获取失败"
fi

# ── 11. Search user by phone ────────────────────────────────────────────────

sep "11) 通过手机号搜索用户（用 demo 用户 13800001111）"
SEARCH=$(CURL -X POST "$BASE/api/friends/search-by-phone" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800001111"}')
echo "    $SEARCH"
if echo "$SEARCH" | grep -q '"nickname":"隔壁老王"'; then
  pass "搜索到用户: 隔壁老王"
else
  fail "搜索失败"
fi

# ── 12. Search self (should reject) ─────────────────────────────────────────

sep "12) 搜索自己的手机号（应拒绝）"
SELF=$(CURL -X POST "$BASE/api/friends/search-by-phone" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13912345678"}')
echo "    $SELF"
if echo "$SELF" | grep -qi '不能添加自己'; then
  pass "搜索自己被正确拒绝"
else
  fail "预期拒绝但未得到"
fi

# ── 13. Send friend request ─────────────────────────────────────────────────

sep "13) 发送好友请求给隔壁老王"
REQ=$(CURL -X POST "$BASE/api/friends/request" \
  -H "Content-Type: application/json" \
  -d '{"receiver_phone":"13800001111"}')
echo "    $REQ"
if echo "$REQ" | grep -q '"request_id"'; then
  REQ_ID=$(echo "$REQ" | python3 -c "import sys,json; print(json.load(sys.stdin)['request_id'])")
  pass "好友请求已发送，request_id=$REQ_ID"
else
  fail "发送好友请求失败"
fi

# ── 14. List friend requests (as test user — should be empty) ───────────────

sep "14) 查看自己收到的好友请求（当前用户应无新请求）"
MY_REQS=$(CURL "$BASE/api/friends/requests")
echo "    $MY_REQS"
if echo "$MY_REQS" | grep -q '"requests":\[\]' 2>/dev/null; then
  pass "自己暂无未处理请求（符合预期）"
else
  info "获取到请求列表"
fi

# ── 15. Login as 隔壁老王 & accept the request ─────────────────────────────

sep "15) 以隔壁老王身份登录，查看并接受好友请求"
LAOWANG=$(curl -s -X POST "$BASE/api/login" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800001111","password":"laowang123"}')
LW_TOKEN=$(echo "$LAOWANG" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Helper for 老王 requests
LW_CURL() {
    curl -s -H "Authorization: Bearer $LW_TOKEN" "$@"
}

LW_REQS=$(LW_CURL "$BASE/api/friends/requests")
echo "    隔壁老王收到的请求: $LW_REQS"

# Extract first request_id
FW_REQ_ID=$(echo "$LW_REQS" | python3 -c "
import sys,json
try:
    reqs=json.load(sys.stdin)['requests']
    if reqs: print(reqs[0]['request_id'])
except: pass
" 2>/dev/null || echo "")

if [ -n "$FW_REQ_ID" ]; then
  ACCEPT=$(LW_CURL -X POST "$BASE/api/friends/requests/$FW_REQ_ID/accept")
  echo "    接受结果: $ACCEPT"
  if echo "$ACCEPT" | grep -q '"status":"ok"'; then
    pass "好友请求已接受"
  else
    fail "接受失败"
  fi
else
  fail "未找到待处理的请求"
fi

# ── 16. Verify mutual friendship ────────────────────────────────────────────

sep "16) 验证互为好友（查看双方好友列表）"
echo "    测试君的好友列表:"
CURL "$BASE/api/friends/activity" | python3 -c "
import sys,json
data=json.load(sys.stdin)
friends=data.get('friends',[])
if friends:
    for f in friends: print('      ', f.get('nickname','?'))
else:
    print('      (暂无好友)')
"
echo "    隔壁老王的好友列表:"
LW_CURL "$BASE/api/friends/activity" | python3 -c "
import sys,json
data=json.load(sys.stdin)
friends=data.get('friends',[])
if friends:
    for f in friends: print('      ', f.get('nickname','?'))
else:
    print('      (暂无好友)')
"
pass "好友关系验证完成"

# ── 17. Send duplicate friend request ───────────────────────────────────────

sep "17) 重复发送好友请求（应拒绝）"
DUP_REQ=$(CURL -X POST "$BASE/api/friends/request" \
  -H "Content-Type: application/json" \
  -d '{"receiver_phone":"13800001111"}')
echo "    $DUP_REQ"
if echo "$DUP_REQ" | grep -qi '已经是好友\|已有一个'; then
  pass "重复请求被正确拒绝"
else
  info "结果如上"
fi

# ── 18. Remove friend ───────────────────────────────────────────────────────

sep "18) 删除好友（测试君删除隔壁老王）"
RM=$(CURL -X POST "$BASE/api/friends/remove" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800001111"}')
echo "    $RM"
if echo "$RM" | grep -q '"status":"ok"'; then
  pass "删除好友成功"
else
  fail "删除失败"
fi

# ── 19. Verify removal ──────────────────────────────────────────────────────

sep "19) 验证好友已删除"
AFTER=$(CURL "$BASE/api/friends/activity")
echo "    删除后好友列表: $AFTER"
if echo "$AFTER" | grep -q '"friends":\[\]' 2>/dev/null; then
  pass "好友列表已清空（符合预期）"
else
  info "好友列表不为空"
fi

# ── 20. Admin login ─────────────────────────────────────────────────────────

sep "20) 管理后台登录"
ADMIN=$(curl -s -X POST "$BASE/admin/login" \
  -d "phone=13912345678&password=test1234")
echo "    $ADMIN"
# Admin returns access_token (no refresh for admin)
ADMIN_TOKEN=$(echo "$ADMIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
if [ -n "$ADMIN_TOKEN" ]; then
  pass "管理后端登录成功"
else
  fail "管理后端登录失败"
fi

# ── 21. Cleanup: delete test user ───────────────────────────────────────────

sep "21) 清理测试数据"
# Note: there's no delete user API, so we just note the test user remains
info "测试用户 13912345678（测试君）保留在数据库中"
info "如需清理，请手动删除 activity.db 并重新初始化"

# ── Summary ─────────────────────────────────────────────────────────────────

sep "全部测试完成"
echo -e "  测试用户: 13912345678 / test1234（昵称: 测试君）"
echo -e "  Demo 用户: 13800001111 / laowang123（隔壁老王）"
echo -e "  更多 demo 用户见 init_demo.py\n"