package com.mycompany;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class MyClassTest {
    @Test
    public void testSayHello() {
        MyClass myClass = new MyClass();
        assertEquals("Hello", myClass.sayHello());
    }
}
