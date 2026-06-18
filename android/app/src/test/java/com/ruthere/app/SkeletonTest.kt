package com.ruthere.app

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Smoke test for the M0 skeleton — verifies the JVM test source set compiles
 * and runs under Gradle. Real unit tests (activity calc, time fuzzing) arrive
 * in M9/M10.
 */
class SkeletonTest {
    @Test
    fun sanity() {
        assertEquals(4, 2 + 2)
    }
}
